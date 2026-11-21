"""Validate data, audit leakage, extract shared features and create development EDA."""

import argparse
from collections import Counter
from pathlib import Path

from app.ml.acquire import DEFAULT_RAW, verify_manifest
from app.ml.dataset import clean_development, load_split, POLICY_VERSION
from app.ml.features import feature_matrix, feature_schema
from app.ml.io import digest, read_json, write_json

DEFAULT_PREPARED = Path("data/processed/devign-v1")
DEFAULT_REPORTS = Path("reports/ml")


def preparation_identity(raw):
    schema = feature_schema()
    code = {name: digest(Path(__file__).parent / name) for name in ("features.py", "dataset.py", "prepare.py", "eda.py")}
    return {"source_manifest_sha256": digest(raw / "manifest.json"), "schema": schema,
            "policy_version": POLICY_VERSION, "implementation": code}


def prepare(raw=DEFAULT_RAW, output=DEFAULT_PREPARED, reports=DEFAULT_REPORTS):
    import numpy as np
    from app.ml.eda import create_eda
    manifest = verify_manifest(raw)
    identity = preparation_identity(raw)
    if (output / "metadata.json").exists():
        metadata = read_json(output / "metadata.json")
        if metadata["identity"] != identity:
            raise ValueError("Preparation inputs changed. Use a new --output directory; existing data are preserved.")
        for filename, expected in metadata["files"].items():
            if digest(output / filename) != expected:
                raise ValueError(f"Prepared file changed: {filename}")
        for filename, expected in metadata["reports"].items():
            if not (reports / filename).is_file() or digest(reports / filename) != expected:
                raise ValueError(f"EDA report missing or changed: {filename}; preserve this run and use fresh output paths")
        return metadata
    train = load_split(raw, "train")
    validation = load_split(raw, "validation")
    test_sources = load_split(raw, "test", include_target=False)
    cleaned, audit, decisions = clean_development(train, validation, test_sources)
    matrices, labels, statuses = {}, {}, {}
    for split in ("train", "validation"):
        rows = cleaned[split]
        if not rows or set(int(row["target"]) for row in rows) != {0, 1}:
            raise ValueError(f"Cleaned {split} must contain both original label classes")
        print(f"Extracting {split}: {len(rows)} functions", flush=True)
        matrices[split], statuses[split] = feature_matrix(row["func"] for row in rows)
        labels[split] = np.array([int(row["target"]) for row in rows], dtype=np.int64)
    output.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(output / "development.npz", X_train=matrices["train"], y_train=labels["train"],
                        X_validation=matrices["validation"], y_validation=labels["validation"])
    write_json(output / "cleaning_decisions.json", decisions)
    write_json(output / "row_index.json", {split: [{"id": row["id"], "parse_status": status} for row, status in zip(cleaned[split], statuses[split])] for split in cleaned})
    write_json(reports / "cleaning_audit.json", audit)
    write_json(reports / "feature_schema.json", identity["schema"])
    create_eda(matrices, labels, statuses, audit, reports)
    metadata = {"identity": identity, "dataset_revision": manifest["revision"],
                "sizes": {split: len(labels[split]) for split in labels},
                "class_counts": {split: dict(Counter(str(int(v)) for v in labels[split])) for split in labels},
                "parse_status": {split: dict(Counter(statuses[split])) for split in statuses},
                "files": {name: digest(output / name) for name in ("development.npz", "cleaning_decisions.json", "row_index.json")},
                "reports": {path.name: digest(path) for path in reports.iterdir() if path.is_file() and path.name not in {"execution_status.json", "model_comparison.json", "test_evaluation.json", "model_metadata.json"}}}
    write_json(output / "metadata.json", metadata)
    return metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW)
    parser.add_argument("--output", type=Path, default=DEFAULT_PREPARED)
    parser.add_argument("--reports", type=Path, default=DEFAULT_REPORTS)
    args = parser.parse_args()
    try:
        metadata = prepare(args.raw_dir, args.output, args.reports)
    except (OSError, ValueError, RuntimeError, ImportError) as exc:
        parser.exit(1, f"Preparation blocked: {exc}\n")
    print(f"Prepared official development data: {metadata['sizes']}")


if __name__ == "__main__":
    main()
