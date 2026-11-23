# Task7C.0 — controlled experiment log

Protocol predeclared in task7c0_ml_baseline.md before any new fitting; exact parameters,
implementation hashes, environment and input hashes locked in
reports/ml/optimization/task7c0-v1/protocol.json. Single seed42,3group-disjoint training
folds, one CPU/BLAS worker,900s cooperative deadline checked between bounded fits.
4CPUs/7.8GiB RAM available; no GPU/new dependency/oversampling/test-set prediction.

11configurations: v1 LR unweighted C.1 /balanced C10; v1RF baseline /deeper unweighted;
v1HGB baseline /regularized unweighted; v2LR balanced; v2RF baseline shape /deeper
unweighted; v2HGB regularized unweighted; v2ExtraTrees160/depth16/leaf4/balanced.
Each is tested in all3training folds. Baseline family defaults are reused; full settings
are in protocol.json, not inferred from display names. Weight/depth/regularization
co-vary in some variants; these are configuration comparisons, not isolated causal
estimates of the effect of class weighting. No resampling was justified for mild imbalance.

Shortlist max mean fold F1 at.5 per family/schema, before validation (7finalists). Then
OOF-only threshold grid.30–.70 step.05: report unconstrained F1 optimum and conservative
operating rule precision>=.50/recall>=.20, otherwise.5. No threshold optimized on validation
or test. Each shortlisted candidate is refit on all cleaned training data, evaluated on
full validation and the predeclared794-row diagnostic, and serialized under ignored
artifacts/devign-optimization/task7c0-v1. Serialization roundtrip scores are checked.

Prediction timing is median5warm full-validation batches, single thread, excluding AST
extraction; baseline uses identical measurement procedure. Feature extraction/cache
wall time is reported separately; it is not end-to-end online latency certification.
No new saved artifact is trusted through public uploads. Strict production loader stays
v1 until explicit deployment acceptance; offline candidates are not auto-promoted.

Recovery: completed per-candidate metrics/OOF checkpoints are reused under identical
protocol. Cache has an extractor/prepared-data receipt; input drift rejects reuse.
Completed report checksums reject altered results. Audit regeneration verifies/reuses
identical existing evidence rather than rewriting timing/NPZ bytes. No random-seed
restarts or adaptive searches after validation viewing. Cooperative timeout is not a
hard per-fit OS kill; tree/iteration/sample bounds constrain individual fits.

Initial unit-test failure incorrectly expected LR n_jobs=None to equal1; lbfgs uses
the outer threadpool limit. Corrected the configuration assertion (unfitted imputer/
classifier and None-or1 worker policy), no benchmark result/feature altered. Focused
new12cases passed before candidate fits. Existing regression suite was511passes.
Final actual runtimes/results, warnings and deployment decision are reported in the
comparison/selection/test documents after completion; no improvement is presumed.

## Completed run

All33grouped-CV fits and7full-training finalist fits completed. Total wall time
186.522s; extraction/setup 53.897s;
fitting, validation, serialization and bootstrap gates 132.020s.
No captured CV fit warnings; no timeout or adaptive retries. Budget900s not exhausted.
All finalists serialize/reload with exact first10validation-row prediction equality.
Numerical gate passers: none. Original model/threshold retained. No test predictions.
A completed-run replay verified checksums and exited without retraining/re-evaluating.

Commands from repository root, activated existing .venv:

```bash
PYTHONPATH=. .venv/bin/python tools/audit_optimization_data.py
PYTHONPATH=. .venv/bin/python -u -m app.ml.optimization.experiment
PYTHONPATH=. .venv/bin/python tools/plot_optimization.py
PYTHONPATH=. .venv/bin/python tools/audit_academic_evidence.py
```

Prepared matrices under data/processed/devign-v1 and raw manifest-pinned data are required.
Ignored audit/feature/OOF/model caches live under artifacts/devign-optimization/task7c0-v1.
Do not change sources/data and reuse the same version: identity mismatch rejects results.
To run a revised protocol, explicitly use a new version and preserve this evidence.
Figures can regenerate from retained cached development predictions without refitting.
The complete.json receipt covers experiment evidence; subsequently generated figures and
selection decision have their own results checksum references.
