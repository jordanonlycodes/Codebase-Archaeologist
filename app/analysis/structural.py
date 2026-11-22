"""Deterministic structural intelligence, independent of ML model availability."""
import ast
from dataclasses import asdict
import hashlib
from pathlib import Path, PurePosixPath

from app.config import STRUCTURAL_LIMITS, STRUCTURAL_THRESHOLDS
from app.analysis.structural_models import (Composition, ComplexitySummary, FileStructure, FunctionStructure,
    HotspotReason, StructuralHotspot, StructuralCoverage, StructuralIntelligence)
from app.analysis.structural_parsers import (Budget, WorkLimit, parse_c, c_definitions, python_definitions,
                                            c_metrics, python_metrics)

DEFINITIONS = {
    'complexity': 'Baseline 1 per valid function, plus documented AST decision points; only valid metrics aggregate.',
    'C': 'Add if, for/while/do, ternary, non-default case label, each &&/||. Switch/default do not add. Count function body only.',
    'Python': 'Add if/elif, for/async-for/while, ternary, each and/or link, except/except*, each non-irrefutable or guarded match case, comprehension generator and filter. Match guard Boolean links count normally. Exclude assert, with, try/finally, else, plain wildcard/capture, pattern alternatives.',
    'nesting': 'Maximum nested control nodes; C if/switch/loop/ternary, Python if/loop/ternary/with/try/handler/match. Else-if adds one; ordinary expressions, cases, Boolean operations and comprehension generators do not add depth.',
    'span': 'Inclusive definition start/end lines; includes comments, blanks and nested definitions; not executable LOC. Python decorators are outside the span.',
    'parameters': 'C declarations excluding lone void and ellipsis; Python positional/keyword-only arguments plus *args/**kwargs including self/cls.',
    'composition': 'Repository composition totals cover classified files only; original inventory retains all-file totals. Physical lines = blank + comment-only + code for covered files. Whitespace-only lines are blank even inside multiline tokens. Mixed code/comment and docstrings count as code. Density = comment-only / nonblank lines on covered files, not a repository quality score.',
    'scope': 'Nested functions/classes/lambdas do not contribute decisions to an enclosing Python function. Lambdas are not separate function records. C extensions/macros lack semantic resolution.',
    'identity': 'SHA256(structural-v1, kind, normalized relative path, language, qualified/name and source line/byte-column range). Stable within identical snapshots; not across arbitrary edits or renames.',
    'coverage': 'C .c and Python .py/.pyi only. All static files retained; non-source files are not_source, other source files unsupported. complete means all included source files received complete supported analysis; not a completeness claim about archive-excluded content.',
    'ML': 'Location-based ml_result_index references defect_risk.functions without changing scores/features; Python and unmatched functions have unavailable ML status.',
}


def identity(kind, path, *symbol):
    normalized = PurePosixPath(path).as_posix()
    return kind+'_'+hashlib.sha256(('structural-v1\0'+kind+'\0'+normalized+'\0'+'\0'.join(map(str,symbol))).encode()).hexdigest()


def band(complexity, thresholds=STRUCTURAL_THRESHOLDS):
    for label, maximum in [('low', thresholds.low_max), ('moderate', thresholds.moderate_max), ('high', thresholds.high_max)]:
        if complexity <= maximum:
            return label
    return 'very_high'


def summarize(functions, thresholds=STRUCTURAL_THRESHOLDS):
    valid = [f for f in functions if f.status == 'analyzed']
    result = ComplexitySummary(analyzed_functions=len(valid))
    if not valid:
        return result
    values = [f.cyclomatic_complexity for f in valid]
    result.total_complexity = sum(values)
    result.average_complexity = sum(values)/len(values)
    result.maximum_complexity = max(values)
    result.maximum_nesting = max(f.max_nesting_depth for f in valid)
    result.high_complexity_functions = sum(v >= thresholds.high_complexity for v in values)
    result.large_functions = sum(f.span_lines >= thresholds.large_span for f in valid)
    result.deeply_nested_functions = sum(f.max_nesting_depth >= thresholds.deep_nesting for f in valid)
    for f in valid:
        result.complexity_bands[f.complexity_band] += 1
    return result


def hotspots(functions, thresholds=STRUCTURAL_THRESHOLDS):
    found = []
    ordered = sorted((f for f in functions if f.status == 'analyzed'),
                     key=lambda f: (-f.cyclomatic_complexity, -f.max_nesting_depth, -f.span_lines, f.path, f.start_line, f.start_column))
    for f in ordered:
        reasons = []
        for metric, limit, label in [('cyclomatic_complexity', thresholds.high_complexity, 'High complexity'),
                                      ('max_nesting_depth', thresholds.deep_nesting, 'Deep control nesting'),
                                      ('span_lines', thresholds.large_span, 'Large function span'),
                                      ('parameter_count', thresholds.many_parameters, 'Many parameters')]:
            value = getattr(f, metric)
            if value >= limit:
                reasons.append(HotspotReason(metric, value, limit, f'{label}: {value} meets review threshold {limit}.'))
        if reasons:
            found.append(StructuralHotspot(f.id, f.file_id, f.path, f.qualified_name or f.name, f.start_line, f.end_line, reasons))
    return found


def composition_from_inventory(file):
    known = file.comment_lines is not None and file.code_lines is not None
    return Composition(file.lines, file.blank_lines, file.comment_lines, file.code_lines,
                       file.comment_lines/file.nonblank_lines if known and file.nonblank_lines else None,
                       'complete' if known else 'unavailable')


def c_composition(data, root, original, budget):
    if root.has_error:
        return original
    comment_ranges = []
    stack = [root]
    while stack:
        node = stack.pop()
        budget.visit()
        if node.type == 'comment':
            comment_ranges.append((node.start_byte, node.end_byte))
        else:
            stack.extend(reversed(node.named_children))
    mask = bytearray(data)
    for start, end in comment_ranges:
        for i in range(start, end):
            if mask[i] not in (10,13):
                mask[i] = 32
    original_lines, code_lines = data.split(b"\n"), bytes(mask).split(b"\n")
    if data.endswith(b"\n"):
        original_lines.pop()
        code_lines.pop()
    comment_only = sum(bool(line.decode("utf-8").strip()) and not code.decode("utf-8").strip()
                       for line,code in zip(original_lines,code_lines))
    nonblank = original.physical_lines-original.blank_lines
    return Composition(original.physical_lines, original.blank_lines, comment_only, nonblank-comment_only,
                       comment_only/nonblank if nonblank else None, 'complete')


def analyze_structure(root, files, *, parsed_files=None, limits=STRUCTURAL_LIMITS, thresholds=STRUCTURAL_THRESHOLDS):
    parsed_files = parsed_files if parsed_files is not None else {}
    coverage = StructuralCoverage(included_files=len(files))
    records, functions = [], []
    for file in sorted(files, key=lambda f:f.path):
        path = PurePosixPath(file.path).as_posix()
        language = 'C' if Path(path).suffix == '.c' else 'Python' if Path(path).suffix in {'.py','.pyi'} else None
        record = FileStructure(identity('file',path), path, language or file.language,
                               'pending' if language else 'unsupported' if file.is_source else 'not_source',
                               composition_from_inventory(file))
        records.append(record)
        if language is None:
            coverage.unsupported_files += int(file.is_source)
            continue
        coverage.supported_files += 1
        if (file.bytes > limits.file_bytes or coverage.parsed_bytes+file.bytes > limits.total_bytes
                or len(functions) >= limits.functions or coverage.visited_nodes >= limits.total_nodes):
            record.status = 'skipped'
            record.reasons.append('resource_limit; undiscovered function count unknown')
            coverage.truncated = True
            continue
        budget = Budget(min(limits.nodes_per_file, limits.total_nodes-coverage.visited_nodes))
        start_index = len(functions)
        try:
            source = root/path
            if source.is_symlink() or not source.resolve().is_relative_to(root.resolve()):
                raise ValueError('unsafe_source')
            with source.open('rb') as handle:
                data = handle.read(limits.file_bytes+1)
            if len(data) > limits.file_bytes or coverage.parsed_bytes+len(data) > limits.total_bytes:
                raise WorkLimit
            coverage.parsed_bytes += len(data)
            text = data.decode('utf-8-sig').replace('\r\n','\n').replace('\r','\n')
            data = text.encode('utf-8')
            line_bytes = [0]
            if language == 'Python':
                for line in text.split('\n'):
                    line_bytes.append(line_bytes[-1]+len(line.encode('utf-8'))+1)
            if language == 'C':
                tree = parse_c(data)
                # Request-local tree/data cache only; no source is serialized.
                parsed_files[path] = (data, tree)
                if tree.has_error:
                    record.reasons.append('parse_errors; independently valid definitions only')
                definitions = c_definitions(tree, budget)
            else:
                tree = ast.parse(text)
                definitions = python_definitions(tree, budget)
            record.status = 'analyzed'
            for node, name, qualified in definitions:
                if len(functions) >= limits.functions:
                    raise WorkLimit
                if language == 'C':
                    start, end, col, endcol = node.start_point.row+1, node.end_point.row+1, node.start_point.column, node.end_point.column
                    size = node.end_byte-node.start_byte
                    valid = not node.has_error
                else:
                    start,end,col,endcol = node.lineno,node.end_lineno,node.col_offset,node.end_col_offset
                    # Conservative span-byte bound, without retaining snippets.
                    size = line_bytes[end]-line_bytes[start-1]
                    valid = True
                f = FunctionStructure(identity('function',path,language,qualified or name,start,end,col,endcol),record.id,
                                      name,qualified or name,path,language,start,end,col,endcol,end-start+1,
                                      'pending' if valid else 'parse_error')
                functions.append(f)
                if not valid:
                    continue
                if size > limits.function_bytes:
                    f.status = 'function_size_limit'
                    coverage.truncated = True
                    continue
                f.__dict__.update(c_metrics(node,budget) if language == 'C' else python_metrics(node,budget))
                f.complexity_band = band(f.cyclomatic_complexity,thresholds)
                f.status = 'analyzed'
            if language == 'C':
                record.composition = c_composition(data,tree,record.composition,budget)
        except WorkLimit:
            record.reasons.append('resource_limit; remaining analysis unknown')
            coverage.truncated = True
            if functions and functions[-1].status == 'pending':
                functions[-1].status = 'work_limit'
        except (ImportError, RuntimeError):
            record.reasons.append('parser_unavailable')
        except (SyntaxError, RecursionError, ValueError, UnicodeError):
            record.reasons.append('parse_failed')
        except OSError:
            record.reasons.append('source_read_failed')
        finally:
            coverage.visited_nodes += min(budget.used,budget.maximum)
        local = functions[start_index:]
        if record.reasons or any(f.status != 'analyzed' for f in local):
            record.status = 'partial' if any(f.status == 'analyzed' for f in local) else 'unavailable'
        elif not local:
            record.status = 'no_functions'
        record.summary = summarize(local, thresholds)
    functions.sort(key=lambda f:(f.path,f.start_line,f.start_column,f.id))
    coverage.analyzed_files = sum(f.status in {'analyzed','no_functions'} for f in records)
    coverage.partial_files = sum(f.status == 'partial' for f in records)
    coverage.skipped_files = sum(f.status in {'skipped','unavailable'} for f in records)
    coverage.invalid_functions = sum(f.status != 'analyzed' for f in functions)
    coverage.composition_files = sum(f.composition.status == 'complete' for f in records)
    covered = [f.composition for f in records if f.composition.status == 'complete']
    coverage.composition_physical_lines = sum(c.physical_lines for c in covered)
    nonblank = sum(c.physical_lines-c.blank_lines for c in covered)
    comments = sum(c.comment_lines for c in covered) if covered else None
    composition = Composition(sum(c.physical_lines for c in covered),sum(c.blank_lines for c in covered),comments,
                              sum(c.code_lines for c in covered) if covered else None,
                              comments/nonblank if covered and nonblank else None,
                              'complete' if covered and len(covered)==len(files) else 'partial' if covered else 'unavailable')
    coverage.complete = bool(coverage.supported_files) and not (coverage.skipped_files or coverage.partial_files or coverage.unsupported_files or coverage.truncated)
    summary = summarize(functions, thresholds)
    status = ('no_supported_files' if not coverage.supported_files else 'partial' if not coverage.complete
              else 'complete' if summary.analyzed_functions else 'no_functions')
    return StructuralIntelligence(status, summary, coverage, composition, records, functions, hotspots(functions,thresholds),
                                  asdict(thresholds),asdict(limits),DEFINITIONS.copy())


def link_ml_results(structure, risk):
    """Only unambiguous (path, line range, name) matches; index into existing results."""
    if risk is None:
        return
    matches = {}
    for index, item in enumerate(risk.functions):
        key = (item.path,item.start_line,item.end_line,item.name)
        matches.setdefault(key,[]).append(index)
    for f in structure.functions:
        indices = matches.get((f.path,f.start_line,f.end_line,f.name),[]) if f.language == 'C' else []
        if len(indices) == 1:
            f.ml_result_index = indices[0]
            f.ml_status = risk.functions[indices[0]].status
