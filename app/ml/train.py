"""Fit three fixed pipelines, select on validation, and evaluate test once.

Completed runs are reused. Candidate checkpoints permit recovery before test
evaluation. A started-but-incomplete test evaluation requires manual review,
never an automatic second look at the holdout.
"""

import argparse
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import time
import warnings

import numpy as np
from threadpoolctl import threadpool_limits

from app.ml.acquire import DEFAULT_RAW, verify_manifest
from app.ml.dataset import audit_test_after_selection, load_split
from app.ml.estimators import build_models, model_parameters, SEED
from app.ml.evaluation import evaluate, select_model, THRESHOLD
from app.ml.features import feature_matrix, feature_schema
from app.ml.io import digest, read_json, write_json
from app.ml.model_store import environment_versions, load_pipeline, save_pipeline
from app.ml.prepare import DEFAULT_PREPARED, DEFAULT_REPORTS, preparation_identity

DEFAULT_RUN = Path("artifacts/devign-v1")


def experiment_identity(raw, prepared):
    return {
        "dataset_manifest_sha256": digest(raw / "manifest.json"),
        "prepared_metadata_sha256": digest(prepared / "metadata.json"),
        "seed": SEED, "threshold": THRESHOLD, "environment": environment_versions(),
        "parameters": {name: model_parameters(model) for name, model in build_models().items()},
        "implementation": {name: digest(Path(__file__).parent / name) for name in (
            "features.py", "dataset.py", "estimators.py", "evaluation.py", "model_store.py", "train.py")},
    }


def test_once(run: Path, selected, raw: Path, selection: dict):
    result_path = run / "test_evaluation.json"
    if result_path.exists():
        return read_json(result_path)
    # Exclusive marker persists through crashes: never silently evaluate twice.
    with (run / "test_evaluation_started.json").open("x", encoding="utf-8") as marker:
        marker.write('{"test_evaluation_started": true}\n')
    test = load_split(raw, "test", include_target=True)
    development = load_split(raw, "train") + load_split(raw, "validation")
    integrity = audit_test_after_selection(test, development)
    X_test, statuses = feature_matrix(row.get("func") for row in test)
    y_test = np.array([int(row["target"]) for row in test], dtype=np.int64)
    probabilities = selected.predict_proba(X_test)[:, 1]  # Exactly one test prediction pass.
    evaluation = {"model": selection["model"], "selected_before_test": True,
                  "evaluations": 1, "metrics": evaluate(y_test, probabilities),
                  "parse_status": dict(Counter(statuses)), "integrity": integrity,
                  "test_rows_modified": 0, "completed_at": datetime.now(timezone.utc).isoformat()}
    write_json(result_path, evaluation)
    return evaluation


def _train(raw, prepared, run, reports):
    source = verify_manifest(raw)
    prepared_metadata = read_json(prepared / "metadata.json")
    if prepared_metadata["identity"] != preparation_identity(raw):
        raise ValueError("Prepared features do not match current source/extractor/cleaning policy")
    for filename, checksum in prepared_metadata["files"].items():
        if digest(prepared / filename) != checksum:
            raise ValueError(f"Prepared file checksum mismatch: {filename}")
    identity = experiment_identity(raw, prepared)
    run.mkdir(parents=True, exist_ok=True)
    identity_path = run / "experiment.json"
    if identity_path.exists():
        if read_json(identity_path) != identity:
            raise ValueError("Experiment inputs changed. Preserve this run; use a different --run-dir for a predeclared new experiment.")
    else:
        if any(run.iterdir()):
            raise ValueError("Run directory contains files without an experiment identity")
        write_json(identity_path, identity)
    if (run / "complete.json").exists():
        for filename, expected in read_json(run / "complete.json")["checksums"].items():
            if digest(run / filename) != expected:
                raise ValueError(f"Completed run artifact changed: {filename}")
        print("Reusing completed run; no model retraining or test evaluation.", flush=True)
        publish_reports(run, reports)
        return read_json(run / "metadata.json")
    with np.load(prepared / "development.npz", allow_pickle=False) as data:
        X_train, y_train = data["X_train"], data["y_train"]
        X_validation, y_validation = data["X_validation"], data["y_validation"]
    comparison = {}
    models = {}
    with threadpool_limits(limits=1):
        for name, pipeline in build_models().items():
            candidate = run / "candidates" / name
            if (candidate / "metrics.json").exists():
                pipeline, _ = load_pipeline(candidate, trusted=True)
                metrics = read_json(candidate / "metrics.json")
            else:
                if candidate.exists() and any(candidate.iterdir()):
                    raise ValueError(f"Incomplete candidate {name}: review before retrying; automatic retraining is disabled")
                candidate.mkdir(parents=True, exist_ok=True)
                write_json(candidate / "fit_started.json", {"model": name, "seed": SEED})
                print(f"Fitting {name} on {len(y_train)} training functions", flush=True)
                started = time.monotonic()
                with warnings.catch_warnings(record=True) as caught:
                    warnings.simplefilter("always")
                    pipeline.fit(X_train, y_train)
                metrics = {"train": evaluate(y_train, pipeline.predict_proba(X_train)[:, 1]),
                           "validation": evaluate(y_validation, pipeline.predict_proba(X_validation)[:, 1]),
                           "fit_seconds": time.monotonic() - started,
                           "parameters": model_parameters(pipeline), "warnings": [str(w.message) for w in caught]}
                metrics["train_validation_f1_gap"] = metrics["train"]["f1"] - metrics["validation"]["f1"]
                save_pipeline(pipeline, candidate, {"model_version": name + "-candidate", "model": name})
                write_json(candidate / "metrics.json", metrics)
            comparison[name] = metrics
            models[name] = pipeline
        selected_name = select_model(comparison)
        selection = {"model": selected_name, "threshold": THRESHOLD, "test_used": False,
                     "rule": "Highest validation F1; exact ties: recall, fewer false positives, smaller absolute train/validation F1 gap, name.",
                     "refit_on_validation": False, "selected_at": datetime.now(timezone.utc).isoformat()}
        write_json(run / "model_comparison.json", comparison)
        write_json(run / "selection.json", selection)
        model_version = "devign-v1-" + digest(identity_path)[:12]
        metadata = save_pipeline(models[selected_name], run, {
            "model": selected_name, "model_version": model_version, "selection": selection,
            "dataset": source["dataset"], "dataset_revision": source["revision"],
            "dataset_license": source["license"], "source_manifest_sha256": digest(raw / "manifest.json"),
            "seed": SEED, "threshold": THRESHOLD, "training": prepared_metadata,
            "prediction_scope": "C function Devign label-1 probability; uncalibrated; dashboard disabled",
        })
        # Reload the saved pipeline before evaluation, verifying the real inference artifact.
        selected, _ = load_pipeline(run, trusted=True)
        test_result = test_once(run, selected, raw, selection)
    metadata["test_evaluation"] = test_result
    metadata["limitations"] = [
        "Syntax counts cannot establish exploitability, dataflow or semantic correctness.",
        "Devign labels are noisy commit-derived research annotations, not vulnerability proofs.",
        "Official splits contain the same projects; exact-function cleaning does not eliminate near duplicates or shared-commit dependence.",
        "Test duplicates/conflicts remain in the untouched official holdout and are reported after selection.",
        "Threshold is fixed at 0.5; probabilities are uncalibrated and not validated on new repositories.",
        "All test rows are scored with train-fitted imputation; the offline inference adapter abstains on invalid or unparseable source.",
    ]
    write_json(run / "metadata.json", metadata)
    files = ["pipeline.joblib", "metadata.json", "feature_schema.json", "selection.json", "model_comparison.json", "test_evaluation.json", "experiment.json"]
    write_json(run / "complete.json", {"checksums": {name: digest(run / name) for name in files}})
    publish_reports(run, reports)
    return metadata


def train(raw=DEFAULT_RAW, prepared=DEFAULT_PREPARED, run=DEFAULT_RUN, reports=DEFAULT_REPORTS):
    run.parent.mkdir(parents=True, exist_ok=True)
    lock = run.parent / ("." + run.name + ".lock")
    try:
        with lock.open("x", encoding="utf-8") as handle:
            handle.write("Experiment in progress; remove only after confirming its process has exited.\n")
    except FileExistsError as exc:
        raise ValueError(f"Experiment is locked: {lock}. Check for a running or interrupted process.") from exc
    try:
        return _train(raw, prepared, run, reports)
    finally:
        lock.unlink(missing_ok=True)


def publish_reports(run, reports):
    for source, destination in (("model_comparison.json", "model_comparison.json"), ("test_evaluation.json", "test_evaluation.json"), ("metadata.json", "model_metadata.json")):
        write_json(reports / destination, read_json(run / source))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW)
    parser.add_argument("--prepared-dir", type=Path, default=DEFAULT_PREPARED)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN)
    parser.add_argument("--reports", type=Path, default=DEFAULT_REPORTS)
    args = parser.parse_args()
    try:
        metadata = train(args.raw_dir, args.prepared_dir, args.run_dir, args.reports)
    except (OSError, ValueError, RuntimeError) as exc:
        parser.exit(1, f"Training blocked: {exc}\n")
    print(f"Selected {metadata['model']}; saved artifacts in {args.run_dir}")


if __name__ == "__main__":
    main()
