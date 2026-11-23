# Task 7C.0 — model comparison

All new scores below use the **same cleaned official validation (2,723 rows)**, previously
used in project development. They are not blind-test or training scores. Full precision,
confusion matrices, average precision (AP), balanced accuracy, runtimes, artifact hashes
and checks are in `reports/ml/optimization/task7c0-v1/results.json`.

## Primary locked operating-threshold comparison

Operating thresholds come exclusively from training grouped OOF predictions on the
predeclared grid, with precision >=0.50 / recall >=0.20 eligibility and fallback 0.5.
The eligibility condition is a training-only development policy, not a validation promise.

| Model / threshold | Accuracy | Precision | Recall | F1 | ROC-AUC | AP |
|---|---:|---:|---:|---:|---:|---:|
| Original RF / 0.5 | 0.568491 | 0.503546 | 0.539696 | 0.520995 | 0.606784 | 0.557827 |
| v1_hgb_baseline / 0.55 | 0.585017 | 0.555328 | 0.228885 | 0.324163 | 0.574578 | 0.538006 |
| v1_lr_balanced_c10 / 0.5 | 0.545722 | 0.471227 | 0.366554 | 0.412352 | 0.536996 | 0.489731 |
| v1_rf_baseline / 0.55 | 0.584649 | 0.551456 | 0.239865 | 0.334314 | 0.606784 | 0.557827 |
| v2_extra_trees / 0.5 | 0.551965 | 0.486003 | 0.527872 | 0.506073 | 0.578960 | 0.491475 |
| v2_hgb_regularized / 0.55 | 0.591994 | 0.584296 | 0.213682 | 0.312925 | 0.602970 | 0.565477 |
| v2_lr_balanced / 0.5 | 0.537642 | 0.467700 | 0.458615 | 0.463113 | 0.544876 | 0.490153 |
| v2_rf_baseline_shape / 0.55 | 0.580610 | 0.533333 | 0.283784 | 0.370452 | 0.601133 | 0.557736 |
| Always positive | 0.434815 | 0.434815 | 1.000000 | 0.606092 | 0.500000 | 0.434815 |

AP means sklearn average precision, not trapezoidal PR-AUC. Scores are uncalibrated.
The always-positive baseline achieves higher F1 than the deployed model by flagging every
function: precision 0.435, specificity zero and AUC 0.5. This makes a claim of superior
F1 versus naive classification unjustified. RF has better ranking discrimination and
accuracy, but practical utility remains limited. Majority-negative F1 is zero and
accuracy 0.565185. These are honest reference baselines, not deployable improvements.

## Fixed 0.5 comparison — report without post-hoc promotion

All seven finalists were also measured at the original, predefined 0.5 threshold.

| Model / threshold | Accuracy | Precision | Recall | F1 | ROC-AUC | AP |
|---|---:|---:|---:|---:|---:|---:|
| v1_hgb_baseline / 0.5 | 0.548660 | 0.482014 | 0.509291 | 0.495277 | 0.574578 | 0.538006 |
| v1_lr_balanced_c10 / 0.5 | 0.545722 | 0.471227 | 0.366554 | 0.412352 | 0.536996 | 0.489731 |
| v1_rf_baseline / 0.5 | 0.568491 | 0.503546 | 0.539696 | 0.520995 | 0.606784 | 0.557827 |
| v2_extra_trees / 0.5 | 0.551965 | 0.486003 | 0.527872 | 0.506073 | 0.578960 | 0.491475 |
| v2_hgb_regularized / 0.5 | 0.584649 | 0.531966 | 0.372466 | 0.438152 | 0.602970 | 0.565477 |
| v2_lr_balanced / 0.5 | 0.537642 | 0.467700 | 0.458615 | 0.463113 | 0.544876 | 0.490153 |
| v2_rf_baseline_shape / 0.5 | 0.564084 | 0.498903 | 0.576014 | 0.534692 | 0.601133 | 0.557736 |

Enhanced RF's F1 0.534692 exceeds original RF by 0.013698, below the predeclared 0.02
minimum. Its AUC is lower (0.601133 versus 0.606784) and precision is below 0.50.
This descriptive result must not be hidden, but does not justify selecting a threshold
post hoc or accepting weaker adoption criteria. OOF-selected 0.55 raised precision and
reduced recall substantially, showing threshold transfer instability.

## Training-only cross-validation

Three stratified group-disjoint folds connect project/commit and exact token shapes.
Fold SD is descriptive variation across three folds, not a confidence interval. Mean
fold F1 at 0.5 shortlists one candidate per family/schema before any validation scores.

| Configuration | Mean fold F1 | Fold SD | OOF operating threshold | Unconstrained OOF F1 threshold | CV fit seconds (3 fits) |
|---|---:|---:|---:|---:|---:|
| v1_hgb_baseline | 0.495665 | 0.004910 | 0.55 | 0.30 | 2.152 |
| v1_hgb_regularized | 0.407525 | 0.000816 | 0.50 | 0.30 | 2.324 |
| v1_lr_balanced_c10 | 0.429706 | 0.010537 | 0.50 | 0.30 | 0.159 |
| v1_lr_unweighted_c01 | 0.172486 | 0.025712 | 0.50 | 0.30 | 0.147 |
| v1_rf_baseline | 0.499483 | 0.010636 | 0.55 | 0.30 | 9.113 |
| v1_rf_deeper_unweighted | 0.398025 | 0.007847 | 0.50 | 0.30 | 19.394 |
| v2_extra_trees | 0.505210 | 0.009078 | 0.50 | 0.30 | 4.059 |
| v2_hgb_regularized | 0.409534 | 0.012676 | 0.55 | 0.30 | 3.261 |
| v2_lr_balanced | 0.485859 | 0.010872 | 0.50 | 0.30 | 0.350 |
| v2_rf_baseline_shape | 0.516543 | 0.005942 | 0.55 | 0.30 | 11.929 |
| v2_rf_deeper_unweighted | 0.406425 | 0.006219 | 0.50 | 0.30 | 42.227 |

Unconstrained F1 optimization generally favors low thresholds; these can approach the
always-positive behavior. The conservative threshold policy was locked before fitting.
No extra threshold or hyperparameter search followed validation viewing. Grouped CV
is stricter than random-row splitting but does not establish unseen-project/time accuracy.
Approximate near-clones are not exhaustively grouped within training.

## Purged diagnostic and uncertainty

Predeclared source-only filtering retains 794 validation rows (347 negative / 447 positive).
Original RF F1 0.574610 and AUC 0.526178 on that subset show much weaker ranking than on
full validation. This is a shifted, conservative diagnostic, not an independent test.

| Candidate at OOF operating threshold | Purged F1 | Paired full-validation F1 delta interval (95%, 200 cluster bootstrap resamples) | Final fit seconds | Median batch prediction seconds (2,723 rows) |
|---|---:|---|---:|---:|
| v1_hgb_baseline | 0.383901 | [-0.231116, -0.160533] | 1.027 | 0.018201 |
| v1_lr_balanced_c10 | 0.488050 | [-0.142808, -0.081301] | 0.081 | 0.001764 |
| v1_rf_baseline | 0.365325 | [-0.216164, -0.154747] | 4.314 | 0.065103 |
| v2_extra_trees | 0.596567 | [-0.036261, 0.006065] | 1.937 | 0.054332 |
| v2_hgb_regularized | 0.328904 | [-0.245458, -0.179319] | 1.293 | 0.033420 |
| v2_lr_balanced | 0.519573 | [-0.088594, -0.029518] | 0.198 | 0.002129 |
| v2_rf_baseline_shape | 0.410480 | [-0.181178, -0.126089] | 5.937 | 0.063983 |

Extra Trees slightly improves purged F1 but has lower full-validation F1 and AUC; its
paired delta interval includes zero. No candidate passes the locked combined gate.
Intervals describe development uncertainty, not multiple-comparison-adjusted confirmation.
Batch prediction excludes parsing and is not a browser/end-to-end latency measurement.

## Historical test evidence — unchanged

Original RF: official test n=2,732, threshold 0.5, accuracy 0.555271, precision 0.515267,
recall 0.537849, F1 0.526316, ROC-AUC 0.587354; matrix [[842,635],[580,675]]. These are
**previously exposed historical test results**, not a new independent confirmation.
Task 7C.0 made zero new test predictions. No new independent dataset was available.

Figures: `cv_comparison.png`, `validation_comparison.png`, `oof_thresholds.png`,
`validation_curves.png`, `validation_confusions.png`, `development_classes.png` in the
versioned report directory. `figures.json` binds them to the results checksum. None
shows a new test curve or proves causal feature importance.
