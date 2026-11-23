# Task 7C.0 — deployment decision

**Retain the original Random Forest; no application model change.**

Model `devign-v1-4a23cc304ca8`, schema `c-function-v1` (11 ordered numeric features),
inclusive score >=0.5 classification. Trusted local artifact:
`artifacts/devign-v1/pipeline.joblib`, SHA256
`9988945c6c851e885f3942a406a4d6c7d704547797e266d6d0aed95520db74e6`.

All seven shortlisted candidates fail the preregistered numerical gate. Original schema
RF threshold tuning sacrifices too much recall. Enhanced-feature RF at fixed 0.5 offers
only +0.013698 validation F1 and lower AUC; it fails the minimum improvement and ranking
requirements even if reconsidered at the original threshold. Extra Trees, strongest at
the OOF-selected operating thresholds, has lower full-validation F1/accuracy/AUC and a
bootstrap delta interval spanning zero. Purged subset improvement alone is insufficient.
These findings do not justify changing the gate after observing scores.

The optimization investigation therefore did not produce sufficiently strong evidence
to replace the deployed model. Original selection among the three historical candidates
remains validation-F1-based, not a claim of excellent generalization or optimality over
all possible algorithms. The all-positive F1 reference and clone/coupling findings must
accompany any scientific interpretation of the modest performance.

Runtime, threshold, frontend, routes, model metadata and strict loader were left intact.
No migration or rollback action is needed; the original artifact and historical reports
remain untouched. Experimental models are isolated in ignored
`artifacts/devign-optimization/task7c0-v1/`; no raw datasets/models were added to Git.
Local candidates roundtrip through joblib and share source-only extraction, but are not
accepted by the production version loader. All 24,473 development rows passed equality
of the experimental first 11 features with the prepared original feature matrices.

A later adoption would need fresh versioned metadata/loader tests, C-only API integration,
rollback acceptance and justified evaluation. None is silently enabled here.
`reports/ml/optimization/task7c0-v1/selection_decision.json` records this decision.
