# Task 7A — University AI requirements compliance audit

## 1. Executive summary and evidence boundary

Audit date: **22 November 2026**. Starting HEAD **5914361742023560edfd7ffff47a0cf556d39a13**,
branch main, equal to local origin/main at entry; tracked tree clean. Three untracked
3D vendor assets were preserved. Remote equality here is a local tracking-reference
check, not a fresh GitHub network observation. Task7A commits are listed in the recovery
record and final completion message.

**Verdict: technically substantiated but not unconditional university submission signoff.**
Requirements1–4 and6 pass on inspected implementation, saved results and successful
checks. Requirement5 is partial under a literal final-test-for-every-candidate reading;
all three were fitted and evaluated on validation, but only RF has final-test metrics.
Requirement7 is integrated/tested in-process, with real browser operation pending.
Requirement8 is partial because the final report/demo/artifact distribution still need
7B/7C/7D work. The group exception requires human confirmation. No demonstrated P0
invalid-experiment or absent-model blocker was found; do not replace or retrain the model.

Evidence is distinguished from assertions: raw/prepared/checkpoint bytes were checked;
cleaning was reproduced; train-derived preprocessing was inspected; actual model inference
ran on original demo source. Existing test names or previous completion reports alone
were not treated as proof. Saved final-test evaluation was read, not repeated. Test-target
class totals were read only for retrospective integrity, not selection/tuning/EDA design.
No academic PDF/DOCX regeneration, cloud-provider setup, UI redesign or roadmap feature
was performed. Existing tiny training-row reproducibility test fits are part of the
unchanged regression suite, not new benchmark training.

## 2. Authoritative eight requirements and group rule

The following exact substantive criteria were supplied by the user. The original
university PDF was not independently available/opened; no extra product roadmap is
substituted for these criteria.

**Group rule:** Each group has three members.

**Requirement 1 — Problem Statement**
- Clearly define the problem.

**Requirement 2 — Dataset**
- Describe the dataset and its source.
- Explain input features and target/output.

**Requirement 3 — Data Preprocessing**
- Handle missing values.
- Remove duplicates.
- Encode categorical data.
- Perform feature scaling if required.
- Split the dataset into training and testing data.

**Requirement 4 — Exploratory Data Analysis**
- Analyze the dataset.
- Use appropriate visualizations and graphs.
- Identify important patterns and relationships.

**Requirement 5 — Train 2 to 4 Machine Learning / Deep Learning / NLP Models**
- Select appropriate models according to the problem.
- Train and test each model.
- Use proper evaluation metrics.

**Requirement 6 — Comparison of Models**
- Compare models using appropriate evaluation metrics.
- Explain why the selected model is the best.
- Understanding of the selected model is mandatory.

**Requirement 7 — Integrate the Model with a Web/Mobile App**
- Deploy the selected model in a functional application.
- Demonstrate how users provide input and receive predictions/results.

**Requirement 8 — Submission**
- GitHub link for source code.
- Project report.
- Dataset/source link.
- Demo of the application.

No approval document was found among tracked project files; untracked entries were only
the three graph assets. README, report cover/body and submission README describe an
individual project with approval **as supplied by the student**, not independent
institutional proof. Preserve Bilal Malik /24P-3061 /SE /5A identity. Obtain instructor
confirmation; do not create fictitious group members or an approval certificate.

## 3. Subrequirement compliance matrix

Full status names are used; conditional N/A does not mean an omitted required operation.
Evidence paths are repository-relative. Commands and symbols are indexed separately.

| ID | Classification | Criterion | Actual evidence | Verification / limitation |
| :-- | :-- | :-- | :-- | :-- |
| 1a | PASS — Verified | Unfamiliar codebases, review problem and expected repository outputs | README.md; tools/generate_report.py: build_pages Problem Statement; submission/*.docx/pdf | Read problem/introduction text in both report formats; inventory/graph/metrics are separate from prediction. |
| 1b | PASS — Verified | Target audience, C-function classification and uncertainty | README.md; app/templates/features/risk.html; docs/inference_api.md | Developer/reviewer workflow, paths/features/classes and uncalibrated estimates are explicit; no confirmed vulnerability claim. |
| 2a | PASS — Verified | Dataset identity, source and format | reports/ml/source_manifest.json; app/ml/acquire.py; data/raw/devign/DATASET_CARD.md | Manifest/file checksums and actual Parquet schema/counts verified; official source linked; source functions not confused with numerical features. |
| 2b | PASS — Verified | Provenance, labels, language and provider-declared attribution | docs/ml_pipeline.md; reports/ml/source_manifest.json; data/raw/devign/C-UDA-1.0.md | Devign-derived FFmpeg/QEMU C functions; target bool label0/1; provider C-UDA declaration verified locally. This is not complete rights clearance for upstream code. |
| 2c | PASS — Verified | Actual sizes, class counts and official partitions | reports/ml/cleaning_audit.json; reports/ml/test_evaluation.json | Raw row/class counts independently read; cleaned development sizes/indexes matched. No new random split. |
| 2d | PASS — Verified | Reproduction and representativeness limitations | app/ml/acquire.py; docs/ml_pipeline.md; reports/ml/README.md | Pinned URLs/checksums and download commands exist. Shared projects/commits, noisy labels, near-clones and external generalization are disclosed. |
| 3a | PASS — Verified | Missing/invalid source and target handling | app/ml/dataset.py: clean_development; tests/ml/test_dataset.py | Recorded raw missing fields/invalid labels are zero; invalid development records have explicit reasons; invalid test labels halt evaluation. |
| 3b | PASS — Verified | Missing numerical features and imputation | app/ml/features.py; app/ml/estimators.py; artifacts/devign-v1/pipeline.joblib | 4029 training /463 validation structural parse failures produce NaN in eight features; saved training medians reproduced and transformed training data finite. |
| 3c | PASS — Verified | Duplicate/conflict removal and leakage audit | app/ml/dataset.py; reports/ml/cleaning_audit.json; data/processed/devign-v1/cleaning_decisions.json | Exactly reproduced all113 removals,54 contradictory development groups and zero normalized cross-split overlaps; near-clone/shared-commit dependence remains. |
| 3d | NOT APPLICABLE WITH JUSTIFICATION | Categorical feature encoding | app/ml/features.py: FEATURE_NAMES; reports/ml/feature_schema.json | All11 model inputs are numerical. project,commit_id,id,target and names are excluded; no categorical predictor requires encoding. Bool target→0/1 is label conversion. |
| 3e | PASS — Verified | Required feature scaling | app/ml/estimators.py; artifacts/devign-v1/candidates/logistic_regression/pipeline.joblib | LR StandardScaler mean/scale reproduce imputed training rows; code fits preprocessing only on X_train. |
| 3f | NOT APPLICABLE WITH JUSTIFICATION | Scaling tree models | app/ml/estimators.py: build_models | RF/HGB use numerical split thresholds and do not require standard scaling. Median imputation remains in both pipelines. |
| 3g | PASS — Verified | Train/validation/test separation and seed | app/ml/prepare.py; app/ml/train.py: test_once; artifacts/devign-v1/selection.json | Official memberships retained, seed42, validation-only selection, test labels omitted from development reads. Final test evaluation guard recorded once. |
| 3h | PASS — Verified | Train/inference feature and decision-rule consistency | app/ml/features.py; app/ml/repository.py; app/ml/model_store.py; tests/test_academic_evidence.py | Shared ordered11 float64 features/parser/schema and saved preprocessing checked; API values match actual pipeline scores. Exact .5 class tie fixed to recorded >=.5 rule. |
| 4a | PASS — Verified | Dataset overview, class balance and missing/duplicate EDA | app/ml/eda.py; reports/ml/split_and_label_counts.png; reports/ml/missing_and_duplicates.png | Real development data and raw integrity statistics; test labels are not development EDA inputs. |
| 4b | PASS — Verified | Function-size/complexity distributions and relationships | reports/ml/feature_distributions.png; reports/ml/feature_correlations.png; reports/ml/features_by_class.png | Saved figures, labels and underlying summary inspected; three original plots visually opened. Pairwise correlations use observed training values. |
| 4c | PASS — Verified | Interpretation and limitations | reports/ml/observations.txt; reports/ml/eda_summary.json; reports/ml/README.md | Size/class medians, skew, parse coverage and feature correlation observations supported; no causality/feature-attribution claim. |
| 5a | PASS — Verified | Train two to four appropriate models | app/ml/estimators.py; artifacts/devign-v1/candidates/*; reports/ml/model_comparison.json | Exactly three candidates with real pipelines, fit markers, parameter records and train/validation metrics; checkpoint hashes verified. |
| 5b | PASS — Verified | Out-of-training evaluation of every candidate | app/ml/train.py; reports/ml/model_comparison.json | Each candidate tested on untouched-by-fit validation rows using accuracy,precision,recall,F1,AUC and confusion matrices. No retuning here. |
| 5c | PARTIAL | Literal final-test metrics for each model | reports/ml/test_evaluation.json; app/ml/train.py: test_once | Only selected RF evaluated on final test. Ask instructor whether validation evaluation for all candidates meets train-and-test-each wording. Do not invent or rerun missing final-test results. |
| 5d | PASS — Verified | Reproducibility, warnings and controls | requirements-ml-frozen.txt; artifacts/devign-v1/experiment.json; app/ml/train.py | Seed42, recorded versions/checksums/hyperparameters, no fit warnings, no search/refit-on-validation; unchanged implementation hashes verified. |
| 6a | PASS — Verified | Compare appropriate metrics without mixing splits | reports/ml/model_comparison.json; reports/ml/test_evaluation.json; tests/test_academic_evidence.py | All candidate validation metrics tabulated; RF held-out results separated. Saved confusion-derived arithmetic verified; AUC not recomputed from holdout scores. |
| 6b | PASS — Verified | Selection justification and selected-model understanding | app/ml/evaluation.py: select_model; docs/ml_pipeline.md; this audit model explanation | RF highest validation F1/recall among three; fewer FP than HGB, more than LR, larger generalization gap. RF not claimed universally best or production-grade. |
| 7a | PASS — Verified | Actual backend input→saved model→results | app/routes/analysis.py: analyze_archive; app/ml/repository.py; tests/ml/test_repository.py | Original mixed ZIP and real trusted RF:2 files,4 structural functions,3 C predictions,7 graph nodes. Direct saved-pipeline score equality verified. |
| 7b | PASS — Verified | GitHub input uses same engine | app/routes/analysis.py: analyze_github; tests/test_github.py: test_shared_api_and_cleanup,test_real_model_github_inference | Mocked fixed-host/pinned archive download plus real shared analysis/model tests pass; not a live GitHub/network verification. |
| 7c | PASS — Verified | Safe unsupported, missing and failed states | tests/ml/test_repository.py; tests/test_academic_evidence.py; tests/test_archive.py | Python-only and JS unscored; malformed C partial; empty ZIP422; invalid ZIP400; missing model unavailable; inference failure partial without invented predictions. |
| 7d | IMPLEMENTED — Not Fully Verified | User-visible browser demonstration and operating server | app/routes/dashboard.py; app/templates/features/risk.html; app/static/risk.js; tests/test_product.py | Real route documents and77 browser-free journeys verified. Chromium/localhost blocked; actual rendered prediction journey and UI acceptance owned by7B. |
| 8a | PASS — Verified | Source GitHub identity/local version control | README.md; .git/config; git status/log/rev-parse commands | Valid origin, main, tracked source present; HEAD matched local origin/main at audit entry. Final audit commits/push are reported separately; no fresh remote proof assumed. |
| 8b | PARTIAL | Current comprehensive academic report | submission/Codebase_Archaeologist_Report.docx; submission/Codebase_Archaeologist_Report.pdf; submission/report_manifest.json | 28-page report,5707 words,9 figures,19 sections,correct identity/metrics exist; current-source validator fails on six stale/missing paths.7C must update, not merely rewrite hashes. |
| 8c | PASS — Verified | Dataset/source link and instructions | README.md; docs/ml_pipeline.md; reports/ml/source_manifest.json | Legitimate provider/revision/license links and pinned download/reproduction instructions. Live HF access not verified; local saved card/checksums intact. |
| 8d | PARTIAL | Portable demonstration/submission readiness | requirements-ml-frozen.txt; docs/task7a_demo_checklist.md; tests/fixtures/university_demo/ | Local genuine API demo works. Fresh clone omits trusted model/raw data;7D must arrange compatible artifact transfer and offline verification. Human browser demo remains7B. |
| G | HUMAN CONFIRMATION REQUIRED | Three-member group rule versus recorded individual status | README.md; submission/README.md; tools/generate_report.py | Solo approval appears only as student-supplied text. No instructor-issued approval file located in repository. Obtain confirmation without manufacturing members/approval. |

## 4. Problem definition and consistency

The product helps developers/reviewers understand unfamiliar source inventories,
structure and observed dependencies, then prioritize manual review. ML solves a narrower
binary task: estimate Devign label1 from numerical C-function syntax features. Outputs
include file/function location, model class/score and coverage; graph/complexity/hotspot
measurements remain source-calculated intelligence rather than trained defect evidence.

README, risk template/JavaScript, inference documentation and report Problem Statement
separate these claims. The report discusses unfamiliar repositories and reviewer limits;
its implementation scope is explicitly Tasks1–3A. Later graph/history functionality is
real but does not remedy any missing academic ML requirement. None of these estimates
establish a confirmed vulnerability or prove a negative-class function safe.

## 5. Dataset and preprocessing findings

Source: **google/code_x_glue_cc_defect_detection**, the CodeXGLUE/Devign C-function dataset,
[official provider](https://huggingface.co/datasets/google/code_x_glue_cc_defect_detection),
recorded revision `69bd48c03223c2104342acd9a807caf61ac3efb8`. Three Parquet shards have
actual schema `id:int32, func:string, target:bool, project:string, commit_id:string`.
The raw `func` text is input to extraction, not a raw-text neural classifier feature.
The original benchmark describes label1 as insecure/defect-related and label0 as its
negative label; application terminology deliberately avoids treating noisy commit-derived
annotations as vulnerability ground truth. Sources are FFmpeg and QEMU, not arbitrary
programming languages or project-independent security examples.

| Split | Raw rows | Raw0 / Raw1 | Retained rows | Retained0 / Retained1 |
| :-- | --: | :-- | --: | :-- |
| Train | 21854 | 11836 /10018 | 21750 | 11786 /9964 |
| Validation | 2732 | 1545 /1187 | 2723 | 1539 /1184 |
| Test | 2732 | 1477 /1255 | 2732 | 1477 /1255 |

Counts/schema came from actual local shards; all source checksums match the manifest.
The saved dataset card declares C-UDA and the preserved agreement is genuine agreement
text. Official CodeXGLUE documentation corroborates provenance/splits and provider
agreement text was consulted. This verifies the **provider declaration/attribution**,
not a blanket license for FFmpeg/QEMU code or legal approval of every redistribution.
Raw data remains Git-ignored with pinned, checksummed acquisition instructions.

Cleaning hashes normalize line endings and outer whitespace only. There are46 raw
training duplicate groups (all contradictory),0 internal validation groups and1 test
duplicate group. Before cleaning, normalized overlaps are8 train/validation,4 train/test,
1 validation/test. All54 contradictory development groups are quarantined (108 rows);
5 further development rows match test sources, for **113 removed rows**. Every decision
and retained official row ID was reproduced, with unchanged labels. Test rows are never
removed; its one contradictory pair remains explicitly disclosed after selection.

All cleaned cross-split normalized overlaps are zero. This is not semantic clone
removal: **1134 train/test**,1132 train/validation and446 validation/test project/commit
pairs remain shared. Test source hashes were consulted for contamination exclusion, so
the test set is a label/evaluation holdout, not a wholly source-blind or project/time
independent benchmark. There is no evidence that this remaining dependence invalidates
all results, but it limits any generalization claim. Do not silently rebuild splits now.

Raw missing fields/invalid labels are zero in recorded shards. Missing numerical values
arise when parsing fails: **4029/21750 training** and **463/2723 validation** snippets lack
eight structural features; three lexical metrics remain observed. Saved training medians
match independent recomputation, and imputed training inputs are finite. Unparseable live
functions abstain instead of inventing values/scores; benchmark evaluation used imputation
on all2732 test rows, including495 unsuccessful parses. Coverage therefore differs.

Eleven ordered numerical inputs: `physical_lines`, `nonblank_lines`, `function_bytes`,
`parameter_count`, `conditional_count`, `loop_count`, `return_count`, `max_nesting_depth`,
`decision_complexity`, `pointer_syntax_count`, `call_count`. Version `c-function-v1`,
float64, Tree-sitter0.25.2 /C grammar0.24.2. No name/ID/project/commit/label is a predictor.
Categorical encoding is N/A. All pipelines use training-fitted median imputation; LR adds
training-fitted StandardScaler, whose mean/scale match training rows. Tree models do not
need scaling. No source log transform or feature selection is applied during fitting.

## 6. EDA evidence and observations

`app/ml/eda.py` creates actual dataset EDA, distinct from application repository heatmaps.
Five development plots plus the selected-model confusion plot are tracked:

| Figure | Data and meaning |
| :-- | :-- |
| reports/ml/split_and_label_counts.png | Official sizes and cleaned development class counts; test labels sealed in development EDA |
| reports/ml/missing_and_duplicates.png | Raw train field missingness and duplicate excess by split |
| reports/ml/feature_distributions.png | Training feature histograms, log1p display only |
| reports/ml/feature_correlations.png | Observed-value pairwise Pearson feature correlations |
| reports/ml/features_by_class.png | Training class-conditional feature boxplots |
| reports/ml/confusion_matrices.png | Selected RF validation/final-test counts, generated from saved metrics |

Machine-readable `eda_summary.json`, cleaning audit and `observations.txt` support the
plots. Three original PNGs (split/labels, distributions, correlations) were opened and
visually inspected during this audit; titles/axes are legible and match the implementation.
Other figures were checked for existence/source references, not claimed visually reviewed.
The existing report embeds nine figures: original/reused EDA panels, confusion matrices
and three workflow diagrams; image relationships resolve. No new EDA was needed.

Training positive fraction is9964/21750=0.458115. Physical-span median is57 lines overall,
55 for class0 versus61 for class1; median observed call count5 versus6. Physical-span
95th percentile359 and max8131 indicate skew. Physical span/decision-complexity correlation
is0.906208; strongest absolute off-diagonal correlation is function_bytes/nonblank_lines,
about0.985328. This is correlation among syntax/size measurements, not causal attribution
or proof that long/complex code is defective. Structural summaries exclude parse-missing
values; class comparison has unequal observed coverage. Test-feature relationships were
not explored for model selection.

## 7. Models, genuine comparison and selected model

Exactly three candidate checkpoints and matching saved metrics exist. Each pipeline was
fitted on21750 cleaned train rows and evaluated on2723 validation rows. Fixed seed42,
threshold0.5, class balancing, one compute thread, no parameter search, no validation
refit and no recorded fit warnings. Candidate checkpoint hashes/metrics match the tracked
comparison; saved experiment/preparation implementation hashes still match current code.

- LR: lbfgs,C1,max_iter2000, median imputation +StandardScaler.
- RF:200 trees,max_depth12,min_samples_leaf3,max_features sqrt,bootstrap,balanced,n_jobs1.
- HGB:160 iterations,learning_rate.08,max_leaf_nodes15,min_samples_leaf20,L2=1,
  balanced,early_stopping=False (no hidden split used for fitting).

**Validation only; not final test:**

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC | TN / FP / FN / TP |
| :-- | --: | --: | --: | --: | --: | :-- |
| Logistic Regression | 0.5453543885420492 | 0.4706521739130435 | 0.3657094594594595 | 0.41159695817490494 | 0.537246127706654 | 1052 /487 /751 /433 |
| Random Forest | 0.5684906353286816 | 0.5035460992907801 | 0.5396959459459459 | 0.5209947003668977 | 0.6067844159949423 | 909 /630 /545 /639 |
| Histogram Gradient Boosting | 0.5486595666544253 | 0.48201438848920863 | 0.5092905405405406 | 0.4952772073921971 | 0.574577592943821 | 891 /648 /581 /603 |

**Selected RF final held-out test only (2732 rows):** accuracy0.5552708638360175,
precision0.5152671755725191, recall0.5378486055776892, F1 **0.5263157894736842**,
ROC-AUC **0.5873540367979673**; confusion `[[842,635],[580,675]]` in TN/FP/FN/TP order.
`test_evaluation.json` records one evaluation and selection before test. Saved confusion
arithmetic/class totals were independently verified; AUC needs original score ranks and
was not recomputed by rerunning holdout predictions. No LR/HGB final-test metrics exist.

RF wins **among these three validation configurations**, primarily on F1/recall. It has
630 FP versus648 HGB and487 LR: improved recall is not free of false positives. Its train
F1=.7334437086092715, validation F1=.5209947003668977, gap=.2124490082423739 suggests
overfitting. Test discrimination remains modest. An always-positive arithmetic baseline
has test F1 about.6295 (but100% FPR); always-negative accuracy about.5406. Thus the selected
model is not universally best, calibrated or production-grade. Baselines are arithmetic
context, not extra trained candidates. Do not retrain to improve the narrative.

### A concise selected-model explanation

A Random Forest combines many decision trees trained on bootstrapped training rows with
random feature subsets at splits. A tree branches using numerical syntax measurements;
the classifier averages tree class estimates into its label1 score. The persisted pipeline
first fills missing features using training medians, then applies200 depth-limited trees.
The app reports that uncalibrated research score and class using the recorded >=.5 rule,
not a confirmed defect or source-level explanation. Counts alone do not capture full
semantics, dataflow, exploitability or unseen-project context. This is sufficient technical
understanding for requirement6; Task8 viva preparation remains separate.

### Requirement5 interpretation needing instructor decision

All candidates were trained and tested **out of training on validation**, which is valid
model selection. The wording may instead require a final test result for every candidate.
Under that strict reading requirement5 is partial. Ask the instructor before final signoff.
If that stricter comparison is required, obtain an explicit approved plan for separately
logged retrospective evaluation of the existing candidates, without retuning/retraining
or claiming the known holdout remains unseen. Do not fabricate missing numbers or do it
silently in Task7A. This is an interpretation/evidence gap, not evidence of an untrained
candidate or leaked-label selection.

## 8. Application integration and actual smoke evidence

`POST /api/analyze` validates a ZIP; `POST /api/analyze/github` validates/downloads a pinned
public archive. Both call `analyze_archive`: secure temporary extraction→inventory→C/Python
structure→shared C features/saved RF→graph→architecture→typed result. Source temporary
files are removed. `.c` only is eligible for ML; no raw dataset or cloud service is needed
for inference. `ModelService` caches trusted local loading and fails safely on missing,
corrupt or incompatible files. No uploaded artifact is deserialized.

`risk.js` consumes `defect_risk`, displays function location, class, estimated score,
features/status, review order and limits. Product workspace restores the same source-free
IndexedDB snapshot across pages and exports whole JSON. Structural hotspots and heatmap
maximum scores retain distinct definitions; no invented repository defect probability.
77 real-document browser-free journeys plus direct API tests cover state/render wiring;
they do not establish actual rendered browser appearance or a human-reviewed demo.

Original demo fixture (not benchmark-labeled data), actual selected model:

| Function | Source | Class | Model estimate |
| :-- | :-- | --: | --: |
| clamp_index | review.c:2–6 | 1 | 0.6446299251115485 |
| sum_values | review.c:8–14 | 0 | 0.4640631119969904 |
| entry | review.c:16–19 | 0 | 0.44115041436869545 |

API result: HTTP200,2 files,4 structural functions,3 scored C functions,7 graph nodes.
`helpers.py` is structurally analyzed, never ML-scored. Each returned feature row/score
was compared directly to the actual persisted pipeline. These fixture estimates prove
integration, not predictive accuracy or known defects. The entry→sum_values call is actual
source evidence, useful for a repository visualization demonstration.

Other executed in-process states: Python-only200/one structural function/no C scores;
JS-only200/zero structural functions/no C scores; empty ZIP422 `empty_repository`;
invalid bytes400 `invalid_archive`; malformed C200/partial/zero scores; missing artifact
unavailable with inventory intact; forced predictor failure200/partial, all three
`inference_failed`, no internal exception text. Missing state is not a low-risk score.
Mocked GitHub plus actual-model tests use the same engine; live GitHub was not verified.

### Focused correction performed

A new boundary regression initially failed: native binary argmax classified p=.5 as0,
where benchmark `evaluate` uses p>=.5 as1. Live output now uses the shared `THRESHOLD` for
class assignment, keeping existing output-shape/class/probability validation. The .49/.5/.51
case passes as0/1/1. For the actual RF this changes exact ties only; probabilities,
features, trained artifacts, saved experiments and displayed research meaning are intact.
No UI redesign or new inference representation was introduced.

## 9. Submission deliverables and vendor inventory

| Deliverable | Inspected state / required closure |
| :-- | :-- |
| Source code | main; valid origin https://github.com/jordanonlycodes/Codebase-Archaeologist; tracked source/tests/docs present. Audit commits/push reported in final response. |
| Environment | Existing .venv works, Python3.14.10 experiment environment; requirements.txt /requirements-ml.txt /requirements-ml-frozen.txt and startup commands exist. Artifact loader requires exact numpy/scipy/sklearn/joblib/parser versions. |
| Trained model | Trusted ignored artifacts/devign-v1/pipeline.joblib, metadata.json, feature_schema.json; all candidate checkpoints local. A fresh clone does NOT carry them.7D must supply secure trusted transfer/restoration and checksums, not training during demo. |
| Dataset | Three ignored legitimate local Parquet shards and card/license; tracked source manifest/reproduction guide. Do not commit raw data. |
| Academic DOCX | submission/Codebase_Archaeologist_Report.docx;5707 words,nine images,editable XML/relationships; correct Bilal identity; actual Word pagination not verified. |
| Academic PDF | submission/Codebase_Archaeologist_Report.pdf;28 A4 pages,19 sections,nine figures; exact saved validation/test values. No fake UI screenshots. |
| Report manifest/validator | Output hashes still match. Source validation fails on six changed/missing paths: app/ml/repository.py,app/routes/analysis.py,app/static/app.js,app/static/risk.js,app/templates/dashboard.html,tests/ml/test_repository.py. Historical validation.json is not a new success record. |
| Demo | Original tests/fixtures/university_demo plus reproducible checklist; API model proof verified. Human browser journey/presentation and offline artifact packaging still required. |
| Group | Individual identity preserved; approval needs instructor-issued confirmation, not inferred from generated text. |

### Three untracked 3D graph assets: runtime, provenance and commit recommendation

- `app/static/vendor/3d-force-graph-1.73.3.min.js`: **required for genuine3D**, loaded lazily
  by `app/static/graph/three.js`;2D/ML work without it. Size691294 bytes, SHA256
  `19b3be27040fc894e56d684d53c5f62526c25e5d27f37e8fe91fafff605e4ef4` matches receipt.
- `3d-force-graph-1.73.3.LICENSE`: not loaded by browser, but required top-level redistribution
  notice. MIT,2017 Vasco Asturiano, matching the consulted pinned upstream license.
- `graph-assets.json`: not loaded by browser; records package/version/fixed npm tarball,
  archive SHA256 and bundle SHA256; useful provenance, not independent authentication.

The installer reads named files only, validates package identity/version and records a
receipt, but does not enforce an independently pinned expected archive digest. The current
bundle has **zero MIT/Copyright/license notices** embedded. Receipt dependency declarations
include Three.js and others as ranges, not an exact resolved third-party license inventory.
Independent npm tarball verification was attempted read-only and blocked by DNS. Therefore
top-level license and local byte consistency pass; complete distribution provenance and
transitive attribution remain **IMPLEMENTED — Not Fully Verified /P2 packaging gap**.

**Recommendation:** vendor these three as one reviewed tracked set for reliable offline
3D distribution, after7D independently verifies archive integrity and supplies exact bundled
third-party license notices. Do not commit only the JS or silently treat its top-level MIT
as proof for every included dependency. **None was staged, deleted or modified in7A.**
The tracked vendor README was corrected to describe optional local installation and this
verification boundary rather than falsely asserting no local assets exist.

## 10. Critical discrepancies and severity

| Priority | Finding | Action / owner |
| :-- | :-- | :-- |
| P0 | No demonstrated absent candidate, invalid evaluation, unverifiable data identity or broken actual-model inference found | Preserve experiment; do not claim absence of all possible bias/leakage. |
| P1 — human academic signoff | Three-member rule lacks documentary solo exception; strict interpretation of train/test every candidate unresolved | Student/instructor: confirm before final submission; no manufactured approval or metrics. |
| P1 — portable submission | Fresh clone omits trusted model; artifact versions tightly checked |7D: secure trusted artifact handoff/backup, exact environment and clean-machine demo; not a local runtime failure. |
| P1 — demonstration evidence | No human-reviewed running browser demo verified here |7B: actual ZIP→risk workflow, local server, visual/accessibility/3D checks; record real captures. |
| P2 — corrected | Native class tie rule differed from recorded inclusive .5 evaluation rule | Localized fix with failing-then-passing boundary regression; no changed scores/artifacts. |
| P2 — report freshness | Tasks1–3A report treats GitHub/graph etc as future, old test counts; source manifest validator fails |7C: update implementation/evidence, current test counts, real screenshots only if captured, regenerated manifest and validators. |
| P2 — historical wording | reports/ml/README.md says Task1 currently invokes no model; immutable metadata says dashboard disabled | Historical Task2 evidence, not current runtime truth. Current ML guide now explicitly explains; do not edit experiment metadata or fake checksums.7C reconcile report wording. |
| P2 — vendor distribution | Receipt consistency/top MIT verified; archive authenticity/transitive notices incomplete |7D packaging review before deciding to track all three assets. |
| P2 — scientific limits | Modest metrics, higher naive-positive F1, shared commits/near-clones, parse/evaluation coverage differences | Already disclosed; retain prominently in7C, not a metric-driven retraining mandate. |
| P3 | Graph centering/camera, responsive and presentation refinements |7B only; no design changes in7A. |

No evidence was found of Python receiving fabricated ML scores, validation metrics
labeled final-test in the recorded tables, fake application screenshots, model training
on random labels, or cloud dependency for the mandatory local ML path. The audit does
not equate complete regression coverage with formal proof of security or generalization.

## 11. Test execution and document validation

- Baseline full suite:502 passed,0 failed/skipped,87.40s, one existing Starlette/httpx warning.
- Read-only `PYTHONPATH=. .venv/bin/python tools/audit_academic_evidence.py`: verified raw
  checksums/schema/counts, cleaning/row IDs, matrices, sample features, training statistics,
  candidate/selected hashes/results and report output hashes. No .fit/held-out prediction.
- New `tests/test_academic_evidence.py`: saved metric arithmetic/schema, original real-model
  ZIP demo, and boundary decision-rule regression. Focused post-fix run:24 passed,0 failed/skipped. Final complete regression:
  **506 passed,0 failed,0 skipped**,87.43s,one existing warning.
- Existing ML/security/GitHub/product/graph/Jordan/history tests are preserved. Node suites
  include77 document journeys,8 history utility,16 store,24 graph,10 architecture,32 impact
  and30 Jordan cases via existing runners; do not add these to Python totals.
- `.venv/bin/python tools/validate_report.py` **failed** first at source hash for
  app/ml/repository.py. This pre-existing stale report check is separate from pytest.
  A read-only XML/Poppler check independently verified both report outputs, all19 sections,
  exact metrics/identity,5707 words,nine images and28 nonempty PDF pages. It did not turn
  the failed current-source validator green or rewrite submission/validation.json.
- No raw data/model/report binaries were committed; ingestion/output/inference guards remain.

## 12. Environment limitations

This sandbox requires the documented polling-selector wrapper for threaded TestClient
runs; application code is not patched for that. Public upstream source pages could be
consulted through the research tool (official CodeXGLUE task and C-UDA, pinned vendor
MIT), while pinned HF/npm pages were not all accessible. Local preserved provider card
and checksums supply actual source evidence. Direct npm archive retrieval failed DNS.
Browser/localhost/live GitHub acceptance and final remote push depend on the environment;
this audit attempted Chromium (exit133,setsockopt denied), Uvicorn (startup complete,
bind127.0.0.1:8000 failed,exit3) and direct GitHub probe (curl6,DNS failed). Results are
recorded in the progress log, never inferred from old tasks.
No live AI/provider test is required for these university ML requirements or performed.

## 13. Next actions, ownership and acceptance

**Before final academic signoff:** obtain solo exception evidence and a decision on whether
validation testing of all candidates plus one selected final holdout meets requirement5.
These human confirmations do not require changing code to begin7B.

**Task7B:** run the local browser demo checklist at1366×768 and narrow widths; validate
import/risk/structure/graph/architecture/heatmap/impact/Jordan/history navigation, actual
3D asset loading and reported camera issues, keyboard flow, no-model/unsupported states,
real screenshots and console. No fabricated visuals or FPS claims.

**Task7C:** rewrite final academic report only after7B evidence. Preserve actual split
names/metrics, explain all three candidates and inclusive decision rule, acknowledge
baseline/generalization limits, update system architecture/test counts, remove stale
future/current contradictions, document instructor decisions without invented identities,
regenerate/check DOCX/PDF and evidence manifest legitimately.

**Task7D:** prepare a reproducible source snapshot, precise environment, dataset source
manifest, trusted selected-artifact delivery/backup and demo instructions. Verify a fresh
checkout can restore inference without retraining; complete vendor integrity/notices and
commit decision, clean-machine/offline acceptance, report validation and safe normal push.
Do not commit secrets, raw datasets or virtual environments. Artifact distribution must
follow the explicit packaging plan, not silently violate current ignore policy.

## 14. Final compliance verdict

**Proceed to Task7B engineering acceptance; do not call the university submission complete.**
Core data, preprocessing, EDA, three-model validation comparison and real C-only inference
are substantiated. No P0 demands a new model experiment before7B. Human group/evaluation
interpretation decisions should be pursued now; browser demonstration, final report
freshness and portable artifact packaging must be closed in7B–7D. This audit is an
implementation/evidence assessment, not institutional approval or a production-security
certification. See the evidence index, demo checklist, JSON summary and progress record.
