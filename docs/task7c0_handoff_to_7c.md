# Task 7C.0 → Task 7C scientific handoff

## Final report values

Application unchanged: Random Forest `devign-v1-4a23cc304ca8`, 11-feature
`c-function-v1`, inclusive threshold >=0.5. C-only research defect-risk scores are
uncalibrated, not confirmed defects/vulnerabilities. Python remains structurally analyzed,
ML-unscored. Original validation F1 0.520995 / AUC 0.606784; original historical exposed-test
F1 0.526316 / AUC 0.587354. Use exact full metrics from `reports/ml/model_comparison.json`
and `reports/ml/test_evaluation.json`; never substitute new CV scores as test results.

## New scientific investigation

11 configurations, three grouped training-only folds, seven full-training finalists,
22-feature experimental source-only extractor, OOF-only fixed threshold grid, 200 paired
cluster-bootstrap development intervals. No new test predictions. All finalists fail
predeclared adoption gate. Enhanced RF fixed-.5 validation F1 0.534692 is a small gain
(+0.013698), with worse AUC 0.601133, not a deployed model. At OOF-selected thresholds,
best new finalist Extra Trees F1 0.506073 is below original RF. Complete comparison and
precision/recall tradeoffs: `docs/task7c0_model_comparison.md`.

Official raw splits 21,854/2,732/2,732; cleaned training 21,750 and validation 2,723;
test unchanged. 113 removed development records, not 113 distinct conflict groups.
54 conflicting normalized-source groups in original cleaning. Fresh source-only audit:
1,816 validation rows share project/commit with training; 233 share normalized token
shape; at least 554 near-shingle matches. Overlap between categories means do not sum.
Purged diagnostic 794 rows, different prevalence, not independent generalization.
Original RF purged AUC 0.526178. Test-source matching was label-blind and descriptive.

## Figures ready

Six actual generated PNGs and checksum manifest in
`reports/ml/optimization/task7c0-v1/`: development_classes, cv_comparison,
validation_comparison (both fixed-.5 and OOF-threshold F1), oof_thresholds,
validation_curves, validation_confusions. All development, no new test curves.
Reproducer `tools/plot_optimization.py`; curves need local ignored prediction caches.
Prior EDA figures remain valid baseline evidence; no academic PDF/DOCX regenerated.

## Mandatory caveats / claims to avoid

The official test has already been exposed. No new blind test or independent external
set was established. Validation was reused and seven finalists compared; uncertainty
intervals are exploratory, not corrected for selection. Token shape is not semantic
equivalence, near-match retrieval is bounded and incomplete, and grouped folds do not
prove new-project/time performance. Always-positive validation F1 0.606092 exceeds RF
F1 at the cost of zero specificity; do not claim universal F1 superiority or high
clinical/security utility. Missing parser features are imputed, not false zero metrics.
No calibration, causal defect indicators, 80–90% accuracy, new language coverage or
successful deployment improvement may be claimed.

## Reproduction / packaging

See experiment log and baseline for commands, environment hashes and runtime. Raw data,
prepared matrices and trusted model are ignored local prerequisites: use existing dataset
fetch/prepare/train instructions for a clean environment, not a downloaded untrusted
joblib. Exact locked checkpoints require pinned artifacts/environment. Task 7D still
owns portable artifact packaging. Old report source-manifest stale references remain
Task 7C work; do not bypass validation by merely changing hashes. Two-member team remains
Bilal Malik (24P-3061) and Aun Anis (24P-3017), per instructor confirmation.

Scientific evidence is ready for final report preparation, with these limitations.
Application visual acceptance from previous stages is not re-certified by offline ML work.
