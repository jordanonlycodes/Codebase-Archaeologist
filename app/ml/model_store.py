"""Trusted local model artifacts; never deserialize uploaded repository files."""

from importlib.metadata import version
from pathlib import Path

from app.ml.features import FEATURE_NAMES, FEATURE_VERSION, feature_schema
from app.ml.io import digest, read_json, write_json


def environment_versions():
    import platform
    names = ["numpy", "scipy", "scikit-learn", "joblib", "tree-sitter", "tree-sitter-c", "pyarrow", "matplotlib", "threadpoolctl"]
    return {"python": platform.python_version(), **{name: version(name) for name in names}}


def save_pipeline(pipeline, directory: Path, metadata: dict):
    import joblib
    directory.mkdir(parents=True, exist_ok=True)
    temporary = directory / "pipeline.joblib.tmp"
    joblib.dump(pipeline, temporary, compress=3)
    temporary.replace(directory / "pipeline.joblib")
    schema = feature_schema()
    write_json(directory / "feature_schema.json", schema)
    result = {**metadata, "feature_version": FEATURE_VERSION,
              "feature_names": list(FEATURE_NAMES), "feature_schema": schema,
              "environment": environment_versions(), "pipeline_sha256": digest(directory / "pipeline.joblib")}
    write_json(directory / "metadata.json", result)
    return result


def load_pipeline(directory: Path, *, trusted: bool = False):
    if not trusted:
        raise ValueError("Joblib can execute code. Only load artifacts you trained or independently trust; pass trusted=True.")
    metadata = read_json(directory / "metadata.json")
    schema = read_json(directory / "feature_schema.json")
    if metadata["feature_version"] != FEATURE_VERSION or metadata["feature_names"] != list(FEATURE_NAMES):
        raise ValueError("Model feature version or ordering is incompatible")
    if schema != feature_schema() or metadata["feature_schema"] != schema:
        raise ValueError("Model extractor schema/parser version is incompatible")
    for package in ("scikit-learn", "numpy", "scipy", "joblib"):
        if metadata["environment"][package] != version(package):
            raise ValueError(f"Model requires {package}=={metadata['environment'][package]}")
    if digest(directory / "pipeline.joblib") != metadata["pipeline_sha256"]:
        raise ValueError("Model checksum mismatch")
    import joblib
    pipeline = joblib.load(directory / "pipeline.joblib")
    if pipeline.n_features_in_ != len(FEATURE_NAMES) or list(pipeline.classes_) != [0, 1]:
        raise ValueError("Model input dimensions or label classes are incompatible")
    return pipeline, metadata
