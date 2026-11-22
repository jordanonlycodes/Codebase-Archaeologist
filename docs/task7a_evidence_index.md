# Task 7A — academic evidence index

Paths below are relative to repository root; links resolve from this document. Local
ignored evidence is deliberately identified as such, not promised in a clean clone.
See [principal audit](task7a_university_compliance_audit.md), [machine summary](task7a_compliance_summary.json),
[demo checklist](task7a_demo_checklist.md) and [progress](task7a_progress.md).

## Authority and identity

- Authoritative university criteria: exact substantive text supplied in Task7A, transcribed
  in the audit. Original PDF was not independently opened; do not cite it as inspected.
- [README.md](../README.md): public project/source/dataset/model explanation and student identity.
- [submission/README.md](../submission/README.md): Tasks1–3A report scope and student-supplied solo claim.
- [tools/generate_report.py](../tools/generate_report.py): identity, Problem Statement,
  selected-model explanation and original report sections. **Not rerun by this audit.**
- No instructor-issued approval document located; generated solo text is not documentary approval.

## R1 — problem and honest outputs

- [README.md](../README.md): Beyond the source; research caveats; workspace workflows.
- [app/templates/features/risk.html](../app/templates/features/risk.html): C-only, uncalibrated estimates.
- [app/static/risk.js](../app/static/risk.js): actual score/class/detail rendering.
- [docs/inference_api.md](inference_api.md): source-calculated metrics versus model estimates.
- Existing report Introduction /Problem Statement /Limitations; both binary paths below.

## R2 — actual dataset

- [app/ml/acquire.py](../app/ml/acquire.py): DATASET,REQUIRED_SCHEMA,EXPECTED_SIZES,
  acquire,verify_manifest; pinned Parquet/card/license downloads and file digests.
- [reports/ml/source_manifest.json](../reports/ml/source_manifest.json): dataset revision,
  immutable URLs, actual bytes/checksums, split names and declared license.
- [app/ml/dataset.py](../app/ml/dataset.py): load_split; schema/count verification.
- [docs/ml_pipeline.md](ml_pipeline.md): dataset attribution, reproduction, license limits.
- Local ignored `data/raw/devign/`: official three Parquet shards, `manifest.json`,
  `DATASET_CARD.md`, `C-UDA-1.0.md`, acquisition plan/status/provider metadata. Actual card
  and agreement verified against local checksums; no raw function bodies copied into audit.
- Official sources consulted: [CodeXGLUE task](https://github.com/microsoft/CodeXGLUE/tree/main/Code-Code/Defect-detection),
  [dataset](https://huggingface.co/datasets/google/code_x_glue_cc_defect_detection),
  [provider agreement](https://raw.githubusercontent.com/microsoft/Computational-Use-of-Data-Agreement/master/C-UDA-1.0.md).
  Live pinned HF page access was blocked; provider metadata/card are preserved locally.

## R3 — preprocessing, leakage and feature consistency

- [app/ml/dataset.py](../app/ml/dataset.py): fingerprint,clean_development,overlap_audit,
  audit_test_after_selection. Test target rejected by development cleaning.
- [app/ml/prepare.py](../app/ml/prepare.py): official split loading, shared feature_matrix,
  development.npz,row_index and per-row decisions; no test targets in prepared arrays.
- [app/ml/features.py](../app/ml/features.py): normalize_source,FEATURE_NAMES,
  extract_features,feature_matrix,feature_schema; deterministic C AST/lexical features.
- [app/ml/estimators.py](../app/ml/estimators.py): imputer/scaler pipelines and seed42.
- [reports/ml/cleaning_audit.json](../reports/ml/cleaning_audit.json): raw/cleaned counts,
  duplicate/conflict/overlap and shared-commit evidence.
- [reports/ml/feature_schema.json](../reports/ml/feature_schema.json):11 ordered float64 fields,
  version/parser/missing-value semantics, excluded inputs.
- Local ignored `data/processed/devign-v1/{development.npz,row_index.json,cleaning_decisions.json,metadata.json}`:
  actual arrays, original IDs,113 decisions and checksums. Reproduced by read-only audit.
- [tests/ml/test_dataset.py](../tests/ml/test_dataset.py): precedence, contradictions,
  sealed targets, duplicates/missingness and invalid labels.
- [tests/ml/test_features.py](../tests/ml/test_features.py): features/order/comments/strings/parser failures.
- [tests/ml/test_model.py](../tests/ml/test_model.py): trusted load, shared inference,
  compatibility, single-evaluation guard and bounded genuine-training-row repeatability tests.
- [tests/test_academic_evidence.py](../tests/test_academic_evidence.py): saved schema/metric
  invariants, actual model API score equality, inclusive .5 decision boundary.

## R4 — dataset EDA (not runtime repository heatmaps)

- [app/ml/eda.py](../app/ml/eda.py): create_eda,describe; cleaned development inputs only.
- [eda_summary.json](../reports/ml/eda_summary.json): original-scale statistics, class
  summaries, parse counts, pairwise correlation matrix and development scope.
- [observations.txt](../reports/ml/observations.txt): actual measured observations/caveats.
- [split_and_label_counts.png](../reports/ml/split_and_label_counts.png): official sizes/development labels.
- [missing_and_duplicates.png](../reports/ml/missing_and_duplicates.png): data quality.
- [feature_distributions.png](../reports/ml/feature_distributions.png): log-display histograms.
- [feature_correlations.png](../reports/ml/feature_correlations.png): training Pearson matrix.
- [features_by_class.png](../reports/ml/features_by_class.png): development target comparisons.
- [confusion_matrices.png](../reports/ml/confusion_matrices.png): RF saved validation/final-test matrices.
- [app/ml/report.py](../app/ml/report.py): saved-results report/plot generation; not rerun.
- [reports/ml/README.md](../reports/ml/README.md): recorded results and baseline context.
  Its final Task3-future wording is historical, not current runtime truth.

## R5/R6 — three candidates, selection and final test

- [app/ml/estimators.py](../app/ml/estimators.py): build_models,model_parameters;
  LogisticRegression,RandomForestClassifier,HistGradientBoostingClassifier.
- [app/ml/train.py](../app/ml/train.py): experiment_identity,_train,test_once; fit only
  X_train, validation selection before target read/final prediction, persisted run guards.
- [app/ml/evaluation.py](../app/ml/evaluation.py): evaluate,select_model,THRESHOLD=.5.
- [model_comparison.json](../reports/ml/model_comparison.json): exact train/validation
  metrics/confusion matrices/configurations/timings/warnings for exactly three candidates.
- [test_evaluation.json](../reports/ml/test_evaluation.json): selected RF only,2732 rows,
  one evaluation, label integrity, class counts and parse statuses.
- [model_metadata.json](../reports/ml/model_metadata.json): selected identity, input hashes,
  versions, feature order, parameters, saved test result and limitations.
- Local ignored `artifacts/devign-v1/`: trusted `pipeline.joblib`, `metadata.json`,
  `feature_schema.json`, `selection.json`, `experiment.json`, `complete.json`,
  `test_evaluation_started.json`, comparison/evaluation records.
- Local ignored `artifacts/devign-v1/candidates/{logistic_regression,random_forest,hist_gradient_boosting}/`:
  each real pipeline,metadata/schema,metrics and fit-start marker; checksums verified.
- Model version `devign-v1-4a23cc304ca8`; selected pipeline SHA256
  `9988945c6c851e885f3942a406a4d6c7d704547797e266d6d0aed95520db74e6`.
- [tools/audit_academic_evidence.py](../tools/audit_academic_evidence.py): repeatable read-only
  integrity/cleaning/matrix/scaler audit. Prints counts/hashes, no source or secrets;
  requires existing local ML evidence. Does not fit or predict the held-out set.
- No LR/HGB final-test evaluation evidence exists; do not extrapolate it from validation.

## R7 — end-to-end actual application

- [app/main.py](../app/main.py): FastAPI, safe errors, static assets and route registration.
- [app/routes/analysis.py](../app/routes/analysis.py): analyze,analyze_github,analyze_archive;
  shared secure scanning/structural/C-only inference/graph/architecture pipeline.
- [app/ingestion/archive.py](../app/ingestion/archive.py), [github.py](../app/ingestion/github.py):
  archive guards, URL validation, fixed upstream destinations/pinned snapshot/cleanup.
- [app/ml/repository.py](../app/ml/repository.py): ModelService,function_nodes,
  analyze_functions; trusted cached loading, bounded extraction, missing/failure states.
- [app/ml/model_store.py](../app/ml/model_store.py): load_pipeline; trust/schema/parser/
  library/checksum/classes/dimension checks before prediction.
- [app/ml/c_model.py](../app/ml/c_model.py): explicit single-C-function inference adapter.
- [app/ml/schemas.py](../app/ml/schemas.py): DefectRisk,FunctionResult,FileIssue response contracts.
- [app/routes/dashboard.py](../app/routes/dashboard.py): actual landing/import/workspace routes.
- [app/static/product/workspace.js](../app/static/product/workspace.js): feature initialization,
  actual response rendering and JSON export.
- [app/static/product/store.js](../app/static/product/store.js): bounded expiring per-tab snapshot lifecycle.
- [tests/ml/test_repository.py](../tests/ml/test_repository.py): real saved model load/cache,
  ZIP/export, no-model/malformed/bad outputs and compatible feature vectors.
- [tests/test_github.py](../tests/test_github.py): shared pipeline, true model with mocked archive,
  malformed URL/redirect/stream limits and cleanup.
- [tests/test_archive.py](../tests/test_archive.py), [test_api.py](../tests/test_api.py):
  preserved archive/API protections.
- [tests/test_product.py](../tests/test_product.py), [frontend/product.test.cjs](../tests/frontend/product.test.cjs):
  actual documents and retained analysis state; browser-free, not genuine visual acceptance.
- [tests/fixtures/university_demo/](../tests/fixtures/university_demo/): original2-file C/Python demo,
 3 C functions,1 Python function. No fabricated ground-truth labels.

## R8 — final deliverables and operational evidence

- [requirements.txt](../requirements.txt), [requirements-ml.txt](../requirements-ml.txt),
  [requirements-ml-frozen.txt](../requirements-ml-frozen.txt): minimal/optional/recorded environment.
- [docs/task7a_demo_checklist.md](task7a_demo_checklist.md): exact startup, ZIP/API/browser steps.
- [submission DOCX](../submission/Codebase_Archaeologist_Report.docx) and
  [PDF](../submission/Codebase_Archaeologist_Report.pdf): original Tasks1–3A report.
- [report_manifest.json](../submission/report_manifest.json),
  [validation.json](../submission/validation.json): historical output/source evidence.
  Current-source validation fails; historical success is not recertified.
- [tools/validate_report.py](../tools/validate_report.py): validator failure reproduced;
  no report generation or validation.json rewrite in7A.
- [docs/frontend.md](frontend.md), [screenshots/README.md](screenshots/README.md): browser
  acceptance boundaries and authentic capture workflow for7B.

## Untracked vendor evidence — do not stage blindly

`app/static/graph/three.js` lazy-loads `app/static/vendor/3d-force-graph-1.73.3.min.js`.
LICENSE/graph-assets.json are distribution/provenance records, not runtime loads. Their
local states, exact hashes, MIT source check and missing transitive notices are documented
in the principal audit. [Installer](../tools/install_graph_assets.py) and
[vendor README](../app/static/vendor/README.md) describe installation/fallback. No untracked
asset was staged/deleted. A receipt alone is not independent npm archive verification.
