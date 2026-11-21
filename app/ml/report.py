"""Publish a readable report from completed artifacts without fitting/evaluating."""

import argparse
from pathlib import Path

from app.ml.acquire import DEFAULT_RAW, verify_manifest
from app.ml.features import FEATURE_NAMES
from app.ml.io import digest, read_json, write_json


def create_report(raw=DEFAULT_RAW, run=Path("artifacts/devign-v1"), reports=Path("reports/ml")):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    for name, checksum in read_json(run / "complete.json")["checksums"].items():
        if digest(run / name) != checksum:
            raise ValueError(f"Completed artifact changed: {name}")
    manifest = verify_manifest(raw)
    comparison = read_json(run / "model_comparison.json")
    evaluation = read_json(run / "test_evaluation.json")
    metadata = read_json(run / "metadata.json")
    eda = read_json(reports / "eda_summary.json")
    audit = eda["audit"]
    write_json(reports / "source_manifest.json", manifest)

    fig, axes = plt.subplots(1, 2, figsize=(9, 4))
    for ax, title, metrics in (
        (axes[0], "Selected model: validation", comparison[metadata["model"]]["validation"]),
        (axes[1], "Selected model: untouched test", evaluation["metrics"]),
    ):
        matrix = metrics["confusion_matrix"]
        ax.imshow(matrix, cmap="Blues")
        for i in range(2):
            for j in range(2):
                ax.text(j, i, str(matrix[i][j]), ha="center", va="center", color="white" if matrix[i][j] > max(map(max, matrix)) * .65 else "black")
        ax.set(xticks=[0, 1], yticks=[0, 1], xticklabels=["0", "1"], yticklabels=["0", "1"],
               xlabel="Predicted label", ylabel="Original label", title=title)
    fig.tight_layout()
    fig.savefig(reports / "confusion_matrices.png", dpi=140)
    plt.close(fig)

    lines = [
        "# Task 2 measured results", "",
        f"Dataset: [{manifest['dataset']}]({manifest['source']}), revision `{manifest['revision']}`. Provider-declared license: **C-UDA**. Source file checksums and licensing URLs are in [source_manifest.json](source_manifest.json).", "",
        "## Dataset and cleaning", "",
        "| Split | Official rows | Retained rows | Label 0 | Label 1 |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for split in ("train", "validation", "test"):
        values = audit["cleaned"][split] if split != "test" else evaluation["integrity"]["test"]
        lines.append(f"| {split} | {audit['raw'][split]['rows']:,} | {values['rows']:,} | {values['labels']['0']:,} | {values['labels']['1']:,} |")
    lines.extend([
        "", f"Development cleaning removed **{audit['removed_rows']} rows**. All rows in {audit['development_conflict_groups']} contradictory development function groups were quarantined; {audit['removal_reason_counts'].get('matches_test_function', 0)} development rows matching test functions were excluded. The raw source files remain unchanged. Each removed row's ID, hash and reasons are recorded under `data/processed/devign-v1/cleaning_decisions.json`.",
        "", "| Official split pair | Identical normalized function groups | Shared project/commit pairs |",
        "| --- | ---: | ---: |",
    ])
    for pair, values in audit["overlap_before"].items():
        lines.append(f"| {pair.replace('__', ' / ')} | {values['function_groups']} | {values['shared_project_commits']} |")
    lines.extend([
        "", "No identical normalized function groups cross the cleaned splits. Shared commits and possible near duplicates remain; this is not a project- or time-independent benchmark.",
        "", f"The untouched test set contains {evaluation['integrity']['test']['normalized_duplicate_groups']} duplicate group and {evaluation['integrity']['test']['contradictory_groups']} conflicting-label group. These labels were inspected only after selecting the model. No test rows were removed.",
        "", "## Shared features", "", ", ".join(f"`{name}`" for name in FEATURE_NAMES) + ".",
        "", "See [feature_schema.json](feature_schema.json) for ordering, definitions, parser versions and missing-value semantics. Features accept C source text only; IDs, project, commit and target never enter the predictor.",
        "", "## EDA observations", "",
    ])
    lines.extend("- " + observation for observation in eda["observations"])
    medians = eda["training_features_by_class"]
    lines.extend([
        f"- Training median physical lines: label 0 = {medians['0']['physical_lines']['quantiles']['median']:.0f}, label 1 = {medians['1']['physical_lines']['quantiles']['median']:.0f}. Median call count: {medians['0']['call_count']['quantiles']['median']:.0f} versus {medians['1']['call_count']['quantiles']['median']:.0f} (observed parses only). These associations are not evidence of causation or exploitability.",
        "", "Plots: [split sizes and development labels](split_and_label_counts.png), [missing values and duplicates](missing_and_duplicates.png), [feature distributions](feature_distributions.png), [correlations](feature_correlations.png), [features by class](features_by_class.png), [selected confusion matrices](confusion_matrices.png).",
        "", "Machine-readable statistics: [eda_summary.json](eda_summary.json), [cleaning_audit.json](cleaning_audit.json). Test labels are intentionally absent from development EDA and recorded separately in [test_evaluation.json](test_evaluation.json).",
        "", "## Validation model comparison", "",
        "All three pipelines were fitted once on cleaned training data, with seed 42, threshold 0.5, training-fitted median imputation, and scaling for Logistic Regression. No parameter search or test tuning was performed.", "",
        "| Model | Accuracy | Precision | Recall | F1 | ROC-AUC | False positives | Train F1 |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ])
    for name in ("logistic_regression", "random_forest", "hist_gradient_boosting"):
        item = comparison[name]
        metrics = item["validation"]
        values = " | ".join(f"{metrics[key]:.4f}" for key in ("accuracy", "precision", "recall", "f1", "roc_auc"))
        lines.append(f"| {name} | {values} | {metrics['false_positives']} | {item['train']['f1']:.4f} |")
    lines.extend([
        "", f"Selected **{metadata['model']}** using highest validation F1. Exact ties would use recall, fewer false positives, smaller absolute training/validation F1 gap, then name. No model was refitted on validation data. The selected model's train/validation F1 gap is **{comparison[metadata['model']]['train_validation_f1_gap']:.4f}**, indicating overfitting risk.",
        "", "## One final test evaluation", "",
        "| Accuracy | Precision | Recall | F1 | ROC-AUC |",
        "| ---: | ---: | ---: | ---: | ---: |",
        "| " + " | ".join(f"{evaluation['metrics'][key]:.4f}" for key in ("accuracy", "precision", "recall", "f1", "roc_auc")) + " |",
        "", f"Confusion matrix `[[TN, FP], [FN, TP]]`: **`{evaluation['metrics']['confusion_matrix']}`**. All {evaluation['metrics']['rows']:,} official test rows were scored in one prediction pass. No rows were dropped for parser errors; missing structural features used training-fitted imputation.",
        "", f"For context, the test label counts imply an always-negative accuracy of {evaluation['metrics']['class_counts']['0'] / evaluation['metrics']['rows']:.4f} and an always-positive F1 of {2 * evaluation['metrics']['class_counts']['1'] / (evaluation['metrics']['rows'] + evaluation['metrics']['class_counts']['1']):.4f} (with a 100% false-positive rate). These are arithmetic baselines, not fitted additional models. The selected model's modest discrimination does not support production vulnerability detection.",
        "", "## Saved artifacts and reproducibility", "",
        f"- Model version: `{metadata['model_version']}`.",
        "- Pipeline: `artifacts/devign-v1/pipeline.joblib` (ignored by Git).",
        f"- Pipeline SHA-256: `{metadata['pipeline_sha256']}`.",
        "- `artifacts/devign-v1/feature_schema.json`, `metadata.json`, `selection.json`, `experiment.json`, `complete.json` and individual candidate checkpoints preserve the run.",
        "- [model_comparison.json](model_comparison.json) includes actual metrics, timings, parameters, warnings and training/validation gaps.",
        "- [model_metadata.json](model_metadata.json) includes package versions, input checksums, code hashes and evaluation provenance.",
        "- Re-running the unchanged training command verifies and reuses the completed run; it does not retrain or re-evaluate test.",
        "", "## Limitations and Task 3", "",
    ])
    lines.extend("- " + limitation for limitation in metadata["limitations"])
    lines.extend([
        "- Raw dataset and pretrained artifacts are not distributed in Git; reproduce locally using the recorded provider revision and environment.",
        "", "Task 3 must extract individual C functions from repository files, call the same feature extractor and explicitly load a trusted artifact. It must show abstentions and model limitations and define repository-level aggregation separately. Task 1 statistics and dashboard routes currently invoke no model. Calibration and evaluation on independent projects are required before claims of practical vulnerability detection.", "",
    ])
    (reports / "README.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW)
    parser.add_argument("--run-dir", type=Path, default=Path("artifacts/devign-v1"))
    parser.add_argument("--reports", type=Path, default=Path("reports/ml"))
    args = parser.parse_args()
    create_report(args.raw_dir, args.run_dir, args.reports)
    print(f"Published measured results to {args.reports / 'README.md'}")


if __name__ == "__main__":
    main()
