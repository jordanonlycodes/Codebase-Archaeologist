# Task 2 pipeline guide

This pipeline uses legitimate CodeXGLUE/Devign C functions and their original labels. It extends `app/ml/`; Task 1 ingestion, static statistics, routes, assets and templates are unchanged.

## Source and licensing

- Dataset: https://huggingface.co/datasets/google/code_x_glue_cc_defect_detection
- Dataset card: https://huggingface.co/datasets/google/code_x_glue_cc_defect_detection/blob/69bd48c03223c2104342acd9a807caf61ac3efb8/README.md
- Original benchmark: https://github.com/microsoft/CodeXGLUE/tree/main/Code-Code/Defect-detection
- Provider license declaration: https://github.com/microsoft/CodeXGLUE#license
- C-UDA agreement: https://github.com/microsoft/Computational-Use-of-Data-Agreement/blob/master/C-UDA-1.0.md
- Tree-sitter bindings: https://github.com/tree-sitter/py-tree-sitter
- C grammar: https://github.com/tree-sitter/tree-sitter-c

The dataset card and CodeXGLUE declare C-UDA for data; CodeXGLUE's software separately declares MIT. The acquisition command checks the declared dataset license before downloading split files. It preserves the provider card and C-UDA text with checksums under `data/raw/devign`. The agreement text is captured from the provider URL and its exact bytes are recorded, even if that upstream URL later changes. Raw source functions and model binaries are not published to GitHub. Dataset licensing is not treated as a blanket license for every underlying source project or future deployment use.

The actual schema is verified using Parquet metadata before loading records: `id: int32`, `func: string`, `target: bool`, `project: string`, `commit_id: string`. Unexpected schemas or official row counts stop processing. The library never executes remote dataset scripts or source functions. PyArrow reads the three small Parquet shards directly; Hugging Face `datasets`, pandas, neural networks and GPUs are unnecessary.

## Reproducing the recorded source

The default acquisition command resolves the current provider revision once and records it. To reproduce this specific run from a fresh checkout, seed the download plan with the tracked source manifest, which includes the immutable dataset URLs and original checksums:

```bash
python -m pip install -r requirements-ml-frozen.txt
mkdir -p data/raw/devign
cp reports/ml/source_manifest.json data/raw/devign/download_plan.json
python -m app.ml.acquire
python -m app.ml.prepare
python -m app.ml.train
python -m app.ml.report
```

Use Python 3.14.10 for the recorded package environment. On other supported Python versions, use `requirements-ml.txt`; results may vary across library/platform versions. Do not copy a manifest over an existing completed dataset directory. Existing completed downloads are checksum-verified and reused without a network request. Failed downloads remain incomplete and never become a training source. The default dataset directory totals about 22 MB compressed.

## Holdout boundary and cleaning policy

1. Preserve the provider files and official split memberships. Never randomly split or shuffle records into new partitions.
2. Load training and validation labels. Load only test `id`, `func`, `project`, and `commit_id` during development; `target` is omitted from the Parquet read.
3. Fingerprint the UTF-8 function after converting CRLF/CR to LF and stripping outer whitespace. Preserve internal whitespace, comments, literals and names. Report exact and normalized duplicates separately. This does not claim semantic clone detection.
4. Quarantine all development records for a normalized function when training/validation labels disagree. Never choose a majority label. The raw records remain preserved.
5. Exclude every training/validation row whose function hash occurs in test, regardless of labels. Test content hashes are used only for contamination removal and integrity counts.
6. Within each development split, retain the first same-label function in official row order. If a non-conflicting function occurs in both development splits, validation takes precedence and training copies are excluded.
7. Quarantine missing/invalid development source and non-binary labels with explicit reasons. Missing project/commit metadata are audited but are not grounds for removing a source function. No imputation is applied to ground-truth labels.
8. Preserve every test row, including duplicates and contradictory labels. After model selection, load its labels, report their quality and evaluate the selected model once. Invalid holdout labels stop evaluation instead of silently reducing the test set.

Every removed development row is logged in `data/processed/devign-v1/cleaning_decisions.json`, with split, original row index, ID, hash and all applicable reasons. The summary is tracked in `reports/ml/cleaning_audit.json`. Raw data has 46 duplicate training groups (all contradictory), no internal validation duplicates, and one duplicate test group. There are 8 train/validation, 4 train/test and 1 validation/test identical groups. All normalized function overlap is eliminated in the cleaned splits. Shared project/commit pairs remain, including 1,134 train/test pairs after cleaning; nearby revisions and semantic clones can still inflate generalization estimates.

## Shared feature contract

Version: **c-function-v1**. Input is one C-function source string; output is an ordered tuple of 11 floats plus a diagnostic parse status. The order is `FEATURE_NAMES` in `app/ml/features.py`, also persisted in `feature_schema.json`.

| Feature | Definition |
| --- | --- |
| `physical_lines` | Lines in newline-normalized, outer-trimmed text, including comments/blanks |
| `nonblank_lines` | Physical lines with non-whitespace content |
| `function_bytes` | UTF-8 byte length of the same normalized snippet |
| `parameter_count` | Declared parameters; exclude lone `void` and variadic ellipsis |
| `conditional_count` | `if`, `switch`, and ternary AST nodes |
| `loop_count` | `for`, `while`, and `do` AST nodes |
| `return_count` | Return-statement AST nodes |
| `max_nesting_depth` | Maximum nested control nodes; an `else if` adds a level |
| `decision_complexity` | 1 + `if` + loops + non-default cases + ternaries + logical `&&` / `||` |
| `pointer_syntax_count` | Pointer declarators, unary address/dereference nodes, and `->` access |
| `call_count` | Call-expression nodes, including macros that parse as calls |

The extractor uses Tree-sitter C 0.24.2 with Python bindings 0.25.2. Comments, strings and multiplication operators do not become control-flow or pointer counts. There is no compiler execution, include resolution, type checking or dataflow analysis.

A valid structural parse requires one function definition and no Tree-sitter errors. Otherwise the three lexical metrics remain available and structural features become NaN. Missing/non-string/invalid-Unicode/oversized (>2 MiB)/NUL input has no fabricated metrics. Invalid source and parsing statuses are diagnostics, not extra predictive columns. No label, project, commit ID, row ID, or function-name vocabulary enters the feature matrix.

Training and offline inference call the exact same `feature_matrix` function. `SimpleImputer(strategy='median', keep_empty_features=True)` is fitted only on training data; its all-empty-column fallback is zero. Logistic Regression then applies training-fitted standard scaling. The two tree models use the imputed numerical values without scaling. The offline inference adapter abstains unless parsing succeeded, while the official evaluation deliberately scores all test rows with imputation; therefore deployment coverage and official benchmark coverage differ.

## EDA and model selection

EDA uses cleaned training and validation source/labels only. Raw test size, non-label missing fields, duplicates and source project counts are integrity diagnostics. Test feature distributions or label-feature comparisons are never inspected to design this experiment. The report's test label counts and confusion matrix are added after selection from the saved evaluation, without rerunning prediction.

Plots cover split counts, development label counts, missing fields, duplicate counts, log-transformed feature histograms, pairwise observed-value Pearson correlations and feature boxplots by class. Machine-readable summaries include original-scale quantiles, means, missingness, parse statuses, class statistics and observations. Training has 17,721 clean parses out of 21,750 snippets; validation 2,260/2,723; test 2,237/2,732. Parse failures are substantial and often reflect fragment/macro syntax unavailable to this parser.

Three configurations are declared in `estimators.py`: Logistic Regression, Random Forest and HistGradientBoostingClassifier. Their complete parameters and fit warnings are in `model_comparison.json`. All use seed 42, class balancing, threshold 0.5 and one compute thread. HistGradientBoosting has `early_stopping=False`; no hidden validation resplit occurs. Each full model is fitted once. There is no hyperparameter search, threshold tuning or post-selection refit.

Selection orders models by highest validation F1, then recall, fewer false positives, smaller absolute training/validation F1 gap, and name. The Random Forest leads the requested models on F1 and recall, with 630 validation false positives versus 648 for HistGradientBoosting and 487 for Logistic Regression. Its larger train/validation F1 gap is reported as a concern. The selected pipeline is saved, reloaded with integrity checks and evaluated on test in one prediction pass. See [measured results](../reports/ml/README.md) for the actual metrics, confusion matrices and baseline context.

## Artifact lifecycle and recovery

- `data/raw/devign/`: three official Parquet files, source metadata, card, license text, download plan and completed manifest.
- `data/processed/devign-v1/`: feature/label arrays, retained-row mapping, per-row cleaning decisions and checksums. No test targets are stored here.
- `artifacts/devign-v1/`: three candidate checkpoints, final pipeline, feature schema, experiment identity, selection, evaluation and completion records.
- `reports/ml/`: small tracked JSON results, six plots, source manifest and readable report.

The experiment identity includes raw/prepared checksums, code hashes, model parameters, random seed and package versions. Repeating an unchanged completed training command verifies checksums and returns existing results. It performs no fit and does not load test labels again. Concurrent runs for the same directory are blocked with an exclusive lock.

Candidate checkpoints allow continuation before the final test phase. A partially fitted candidate or a test-started marker without a completed evaluation causes an explicit stop. Investigate the failure; do not delete the evaluation marker to repeatedly inspect the holdout. A crashed process can leave `artifacts/.devign-v1.lock`; remove that lock only after confirming the process exited. Changing experimental inputs requires a deliberately new run directory, not overwriting prior evidence. Later experiments on this benchmark cannot claim the test set is still unseen by the developer.

Joblib is executable serialization. `LocalCFunctionModel(path, trusted=True)` is only for locally trained or independently trusted artifacts. Loading checks feature order/version, parser version, numerical library versions, checksum, feature count and classes before prediction. Never load artifacts from ZIP uploads or other untrusted source repositories. Task 2 provided only offline loading; Task 3A now uses the same loader in its cached repository service.

## Tests

With optional dependencies installed:

```bash
python -m pytest -q
python -m pip check
python -m compileall -q app tests
```

120 tests pass in the recorded environment: all 73 Task 1 tests and 47 ML tests. Features, ordering, malformed input, literal/comment handling, parse failures, duplicate precedence, contradiction quarantine, missing data, test sealing, reproducibility, cache verification, metric formulas, model compatibility, trusted loading and the single-evaluation guard are covered. Two bounded Logistic Regression test fits use only 128 authentic training rows to verify repeatability; they are not benchmark experiments. No model is trained with artificial labels. Small logic fixtures in cleaning/metric tests are never used as training data. If ML dependencies or genuine data are absent, relevant optional tests explicitly skip and the dashboard remains runnable.

In the restricted development sandbox, local socket wake-up writes are unavailable. The application tests were run with this process-local selector workaround; it changes no application code or predictions:

```bash
python - <<'PY'
import selectors
import pytest
OriginalSelector = selectors.DefaultSelector
class PollingSelector(OriginalSelector):
    def select(self, timeout=None):
        return super().select(0.02 if timeout is None else min(timeout, 0.02))
selectors.DefaultSelector = PollingSelector
raise SystemExit(pytest.main(['-q']))
PY
```

## Task 3A integration

Task 3A now implements Tree-sitter C function boundaries and file/line locations, shared feature extraction, trusted cached Random Forest loading, parsing abstention and explicitly uncalibrated function scores. See [the inference API guide](inference_api.md). The selected model and benchmark results have not changed. A repository-level score needs a separate justified aggregation contract; `AnalysisResult` totals cannot substitute for C function source. Independent-project evaluation and calibration are still required before practical security claims. The current test ROC-AUC of 0.5874 and 635 false positives demonstrate this limitation.

The repository service calls `extract_features` for each extracted definition and constructs float64 rows in `FEATURE_NAMES` order, identical to `feature_matrix`. It reuses the saved imputer and estimator without fitting. Only parseable functions are scored; individual valid functions can still be scored from a file containing other parse errors, with a file-level warning. Task 3B academic documentation is provided in submission/; document generation does not alter the experiment.
