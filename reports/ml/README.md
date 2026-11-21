# Task 2 measured results

Dataset: [google/code_x_glue_cc_defect_detection](https://huggingface.co/datasets/google/code_x_glue_cc_defect_detection), revision `69bd48c03223c2104342acd9a807caf61ac3efb8`. Provider-declared license: **C-UDA**. Source file checksums and licensing URLs are in [source_manifest.json](source_manifest.json).

## Dataset and cleaning

| Split | Official rows | Retained rows | Label 0 | Label 1 |
| --- | ---: | ---: | ---: | ---: |
| train | 21,854 | 21,750 | 11,786 | 9,964 |
| validation | 2,732 | 2,723 | 1,539 | 1,184 |
| test | 2,732 | 2,732 | 1,477 | 1,255 |

Development cleaning removed **113 rows**. All rows in 54 contradictory development function groups were quarantined; 5 development rows matching test functions were excluded. The raw source files remain unchanged. Each removed row's ID, hash and reasons are recorded under `data/processed/devign-v1/cleaning_decisions.json`.

| Official split pair | Identical normalized function groups | Shared project/commit pairs |
| --- | ---: | ---: |
| train / test | 4 | 1135 |
| train / validation | 8 | 1137 |
| validation / test | 1 | 446 |

No identical normalized function groups cross the cleaned splits. Shared commits and possible near duplicates remain; this is not a project- or time-independent benchmark.

The untouched test set contains 1 duplicate group and 1 conflicting-label group. These labels were inspected only after selecting the model. No test rows were removed.

## Shared features

`physical_lines`, `nonblank_lines`, `function_bytes`, `parameter_count`, `conditional_count`, `loop_count`, `return_count`, `max_nesting_depth`, `decision_complexity`, `pointer_syntax_count`, `call_count`.

See [feature_schema.json](feature_schema.json) for ordering, definitions, parser versions and missing-value semantics. Features accept C source text only; IDs, project, commit and target never enter the predictor.

## EDA observations

- Cleaning retained 21750 training and 2723 validation rows; removed 113 development rows.
- Training label 1 fraction is 0.4581; this is a dataset prevalence, not repository risk.
- Tree-sitter parsed 17721 of 21750 training snippets without errors; structural failures are missing values, not zeros.
- Test labels and test feature distributions were not used for development EDA.
- Official splits share projects; identical-function removal does not establish project-, time- or commit-independent generalization.
- Strongest absolute training feature correlation: function_bytes / nonblank_lines, Pearson r=0.9853.
- Training median physical lines: label 0 = 55, label 1 = 61. Median call count: 5 versus 6 (observed parses only). These associations are not evidence of causation or exploitability.

Plots: [split sizes and development labels](split_and_label_counts.png), [missing values and duplicates](missing_and_duplicates.png), [feature distributions](feature_distributions.png), [correlations](feature_correlations.png), [features by class](features_by_class.png), [selected confusion matrices](confusion_matrices.png).

Machine-readable statistics: [eda_summary.json](eda_summary.json), [cleaning_audit.json](cleaning_audit.json). Test labels are intentionally absent from development EDA and recorded separately in [test_evaluation.json](test_evaluation.json).

## Validation model comparison

All three pipelines were fitted once on cleaned training data, with seed 42, threshold 0.5, training-fitted median imputation, and scaling for Logistic Regression. No parameter search or test tuning was performed.

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC | False positives | Train F1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| logistic_regression | 0.5454 | 0.4707 | 0.3657 | 0.4116 | 0.5372 | 487 | 0.4308 |
| random_forest | 0.5685 | 0.5035 | 0.5397 | 0.5210 | 0.6068 | 630 | 0.7334 |
| hist_gradient_boosting | 0.5487 | 0.4820 | 0.5093 | 0.4953 | 0.5746 | 648 | 0.6064 |

Selected **random_forest** using highest validation F1. Exact ties would use recall, fewer false positives, smaller absolute training/validation F1 gap, then name. No model was refitted on validation data. The selected model's train/validation F1 gap is **0.2124**, indicating overfitting risk.

## One final test evaluation

| Accuracy | Precision | Recall | F1 | ROC-AUC |
| ---: | ---: | ---: | ---: | ---: |
| 0.5553 | 0.5153 | 0.5378 | 0.5263 | 0.5874 |

Confusion matrix `[[TN, FP], [FN, TP]]`: **`[[842, 635], [580, 675]]`**. All 2,732 official test rows were scored in one prediction pass. No rows were dropped for parser errors; missing structural features used training-fitted imputation.

For context, the test label counts imply an always-negative accuracy of 0.5406 and an always-positive F1 of 0.6295 (with a 100% false-positive rate). These are arithmetic baselines, not fitted additional models. The selected model's modest discrimination does not support production vulnerability detection.

## Saved artifacts and reproducibility

- Model version: `devign-v1-4a23cc304ca8`.
- Pipeline: `artifacts/devign-v1/pipeline.joblib` (ignored by Git).
- Pipeline SHA-256: `9988945c6c851e885f3942a406a4d6c7d704547797e266d6d0aed95520db74e6`.
- `artifacts/devign-v1/feature_schema.json`, `metadata.json`, `selection.json`, `experiment.json`, `complete.json` and individual candidate checkpoints preserve the run.
- [model_comparison.json](model_comparison.json) includes actual metrics, timings, parameters, warnings and training/validation gaps.
- [model_metadata.json](model_metadata.json) includes package versions, input checksums, code hashes and evaluation provenance.
- Re-running the unchanged training command verifies and reuses the completed run; it does not retrain or re-evaluate test.

## Limitations and Task 3

- Syntax counts cannot establish exploitability, dataflow or semantic correctness.
- Devign labels are noisy commit-derived research annotations, not vulnerability proofs.
- Official splits contain the same projects; exact-function cleaning does not eliminate near duplicates or shared-commit dependence.
- Test duplicates/conflicts remain in the untouched official holdout and are reported after selection.
- Threshold is fixed at 0.5; probabilities are uncalibrated and not validated on new repositories.
- All test rows are scored with train-fitted imputation; the offline inference adapter abstains on invalid or unparseable source.
- Raw dataset and pretrained artifacts are not distributed in Git; reproduce locally using the recorded provider revision and environment.

Task 3 must extract individual C functions from repository files, call the same feature extractor and explicitly load a trusted artifact. It must show abstentions and model limitations and define repository-level aggregation separately. Task 1 statistics and dashboard routes currently invoke no model. Calibration and evaluation on independent projects are required before claims of practical vulnerability detection.
