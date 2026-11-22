"""Bounded C-only inference over files accepted by the static scanner."""
from dataclasses import dataclass
from pathlib import Path
from threading import Lock
import os
import math
from app.ml.schemas import DefectRisk, FileIssue, FunctionResult

from app.ml.features import FEATURE_NAMES, _language, extract_features


@dataclass(frozen=True)
class InferenceLimits:
    functions: int = 1000
    file_bytes: int = 512 * 1024
    total_bytes: int = 8 * 1024 * 1024
    function_bytes: int = 128 * 1024


class ModelService:
    """Only operator configuration determines the artifact path; failures are cached."""
    def __init__(self, directory=None):
        self.directory = Path(directory or os.environ.get('ARCHAEOLOGIST_MODEL_DIR') or
                              Path(__file__).resolve().parents[2] / 'artifacts/devign-v1')
        self.lock = Lock()
        self.loaded = False
        self.pipeline = None
        self.metadata = {}

    def load(self):
        with self.lock:
            if not self.loaded:
                try:
                    from app.ml.model_store import load_pipeline
                    pipeline, metadata = load_pipeline(self.directory, trusted=True)
                    from sklearn.ensemble import RandomForestClassifier
                    if not isinstance(pipeline.steps[-1][1], RandomForestClassifier):
                        raise ValueError('Expected selected Random Forest')
                    if not callable(getattr(pipeline, 'predict_proba', None)):
                        raise ValueError('Probability inference unsupported')
                    if not isinstance(metadata.get('model_version'), str):
                        raise ValueError('Missing version')
                    self.pipeline, self.metadata = pipeline, metadata
                except Exception:
                    # Never expose operator paths or deserializer exception text to clients.
                    self.pipeline = None
                self.loaded = True
        return self.pipeline


SERVICE = ModelService()


def function_nodes(data, parsed_root=None):
    from tree_sitter import Parser
    root = parsed_root if parsed_root is not None else Parser(_language()).parse(data).root_node
    stack = [root]
    def definitions():
        while stack:
            node = stack.pop()
            if node.type == 'function_definition':
                yield node
            else:
                stack.extend(reversed(node.named_children))
    return root.has_error, definitions()


def function_name(node):
    declarator = node.child_by_field_name('declarator')
    while declarator is not None:
        if declarator.type == 'identifier':
            return declarator.text.decode('utf-8')
        declarator = declarator.child_by_field_name('declarator')
    return None


def analyze_functions(root, files, service=None, limits=InferenceLimits(), *, parsed_files=None):
    service = service or SERVICE
    eligible = [f for f in files if Path(f.path).suffix == '.c']
    result = DefectRisk('no_functions', 'No eligible C function definitions found.',
                        eligible_files=len(eligible),
                        unsupported_source_files=sum(f.is_source and Path(f.path).suffix != '.c' for f in files))
    if not eligible:
        return result
    pipeline = service.load()
    if pipeline is None:
        result.status = 'unavailable'
        result.message = 'Model unavailable. Restore trusted compatible artifacts and restart the server; static analysis is complete.'
        return result
    result.model_version = service.metadata['model_version']
    consumed = 0
    pending, matrix = [], []
    for file in eligible:
        if len(result.functions) >= limits.functions:
            result.file_issues.append(FileIssue(file.path, 'function_limit_reached; remaining count unknown'))
            continue
        if file.bytes > limits.file_bytes or consumed + file.bytes > limits.total_bytes:
            result.file_issues.append(FileIssue(file.path, 'source_size_limit; function count unknown'))
            continue
        try:
            path = root / file.path
            if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
                raise ValueError('Unsafe source')
            data = path.read_bytes()
            consumed += len(data)
            if len(data) > limits.file_bytes or consumed > limits.total_bytes:
                raise ValueError('Source changed')
            # Match scanner decoding and retain original line numbering.
            data = data.decode('utf-8-sig').replace('\r\n', '\n').replace('\r', '\n').encode('utf-8')
            cached = (parsed_files or {}).get(file.path)
            parsed_root = cached[1] if cached is not None and cached[0] == data else None
            has_error, nodes = function_nodes(data, parsed_root)
            if has_error:
                result.file_issues.append(FileIssue(file.path, 'parse_errors; only independently valid functions may be scored'))
            for node in nodes:
                if len(result.functions) >= limits.functions:
                    result.file_issues.append(FileIssue(file.path, 'function_limit_reached; remaining count unknown'))
                    break
                item = FunctionResult(function_name(node), file.path, node.start_point.row + 1,
                                      node.end_point.row + 1, 'function_size_limit')
                result.functions.append(item)
                if node.end_byte - node.start_byte > limits.function_bytes:
                    continue
                features = extract_features(data[node.start_byte:node.end_byte].decode('utf-8'))
                item.features = features.as_dict()
                item.status = features.parse_status
                if features.parse_status == 'ok':
                    pending.append(item)
                    matrix.append(features.values)
        except Exception:
            result.file_issues.append(FileIssue(file.path, 'extraction_failed; function count unknown'))
    if pending:
        try:
            import numpy as np
            values = np.asarray(matrix, dtype=np.float64).reshape(-1, len(FEATURE_NAMES))
            probabilities = pipeline.predict_proba(values)
            classes = pipeline.predict(values)
            if probabilities.shape != (len(pending), 2) or len(classes) != len(pending):
                raise ValueError('Invalid output shape')
            if any(not math.isfinite(float(p)) or not 0 <= p <= 1 for p in probabilities.flat):
                raise ValueError('Invalid probability')
            if any(c not in (0, 1) for c in classes):
                raise ValueError('Invalid class')
            for item, probability, label in zip(pending, probabilities[:, 1], classes):
                item.status = 'analyzed'
                item.model_probability = float(probability)
                item.predicted_class = int(label)
        except Exception:
            for item in pending:
                item.status = 'inference_failed'
    result.analyzed_functions = sum(f.status == 'analyzed' for f in result.functions)
    result.defect_related = sum(f.predicted_class == 1 for f in result.functions)
    result.non_defect_related = sum(f.predicted_class == 0 for f in result.functions)
    result.skipped_functions = len(result.functions) - result.analyzed_functions
    if result.file_issues or result.skipped_functions:
        result.status, result.message = 'partial', 'Partial coverage. Review function statuses and file issues; unparsed function counts are unknown.'
    elif result.analyzed_functions:
        result.status, result.message = 'ready', 'C function analysis complete. Estimated model probabilities are uncalibrated; predictions are not confirmed vulnerabilities.'
    return result
