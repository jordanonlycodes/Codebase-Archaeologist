# Task7C.0 — verified scientific baseline and preregistered budget

Start:main at f24743bd79ac30a0b9132d5b63e923944adf38bb. No tracked changes; three original
untracked graph vendor assets preserved. Baseline **511passed,0failed/skipped,102.70s**,
one existing Starlette/httpx warning. Normal command `.venv/bin/python -m pytest -q`;
restricted sandbox uses the process-local polling selector wrapper in7B.1 baseline.

Read-only `PYTHONPATH=. .venv/bin/python tools/audit_academic_evidence.py` passed actual
raw/checkpoint digests, cleaning reproduction, row IDs, matrix/schema parity and trained
imputer/scaler statistics. No benchmark model fit or test prediction was performed.

## Dataset / deployed pipeline

CodeXGLUE/Devign, google/code_x_glue_cc_defect_detection, pinned revision
69bd48c03223c2104342acd9a807caf61ac3efb8. Source:
https://huggingface.co/datasets/google/code_x_glue_cc_defect_detection . Local manifest
records c-uda with card/license files; preserve attribution and upstream restrictions.
Official train21854/validation2732/test2732. Clean train21750 (11786class0/9964class1),
validation2723 (1539/1184); test2732 unchanged.113development cleaning removals. Test class
counts1477/1255 are historical evidence, not new development inputs. Raw C text is input;
numeric features are predictors; dataset binary defect-related labels are the target.

Version c-function-v1 has11ordered numeric features: physical_lines,nonblank_lines,
function_bytes,parameter_count,conditional_count,loop_count,return_count,max_nesting_depth,
decision_complexity,pointer_syntax_count,call_count. Only valid exactly-one-function parses
receive structural measurements. Training4029/21750 and validation463/2723 rows have missing
structural values (not zero); lexical values remain. Median imputation is fitted only on
training data; LR additionally uses training-fitted scaling, tree models do not need it.
Raw sizes:44,393,835train bytes,5,416,329validation bytes,5,480,526test-source bytes; largest
snippet142346bytes. Source-length medians935/928/966bytes respectively, before cleaning.

Three original fixed pipelines were trained (seed42): LR C1balanced/lbfgs; RF200trees,
depth12,leaf3,sqrt features,balanced; HGB lr.08,160iterations,15leaves,minleaf20,L2=1,
balanced,noearlystopping. Recorded original fit times .1752/5.5171/1.5927seconds respectively.
Saved exact validation metrics remain reports/ml/model_comparison.json. RFvalidation
F1=.5209947003668977,AUC=.6067844159949423; selected RF held-out F1=.5263157894736842,
AUC=.5873540367979673 in test_evaluation.json. Those are historical exposed-test results.

Selected trusted local artifact artifacts/devign-v1/pipeline.joblib (~4.3MiB), model
version devign-v1-4a23cc304ca8, SHA256
9988945c6c851e885f3942a406a4d6c7d704547797e266d6d0aed95520db74e6.
Strict loader checks schema/parser/library versions and digest; C-only inference shares
feature_matrix/extract_features, validates probability/class shapes and labels score>=.5.
Missing model/malformed/unsupported source gives unavailable/partial/unscored, never fake
predictions. Risk/graph/heatmap/Jordan use returned actual C-only scores/classes. Existing
ML/API/academic evidence/frontend regressions protect this contract.

## Locked development protocol — before new candidate fits

4available CPUs,7.8GiB physical RAM/~4.2GiB available; use one sklearn/BLAS worker and
at most11configurations ×3training-only grouped folds plus7family/schema finalists.
Bounded trees/iterations and900second cooperative fit budget, not unrestricted search.
No new dependency. Enhanced features cached separately; raw/prepared/v1 artifacts remain.

Training-only CV groups connect project+commit and exact alpha-normalized token clones.
Exact/near-clone analysis uses test **source only**, never test labels. Whole official
validation remains the primary, explicitly reused development gate; separately report a
label-independent purged validation subset excluding training project/commit, canonical
clone and confirmed approximate-near-clone matches. Do not silently rewrite any split.

Use CVF1 at.5 to shortlist one candidate per family/schema, then select thresholds using
training OOF only on fixed grid .30,.35,…,.70. Report unconstrained F1 optimum, but the
operating threshold requires OOFprecision>=.50/recall>=.20 (else.5). Compare all-positive
and majority baselines explicitly. All shortlisted validation results are reported once;
no adaptive configuration changes after viewing them. A single predeclared selection
among7finalists is development evidence, not independent generalization confirmation.

Deployment requires validation F1 gain>=.02, positive lower95% paired cluster-bootstrap
F1 delta, precision>=.50, AUC>=original baseline, accuracy within.01 of original, balanced
accuracy no worse, and nonnegative F1 delta on >=300purged validation rows. Also require
safe serialization/feature parity, <=16MiB candidate artifact and <=25ms/function and
<=2×baseline batch inference latency. Do not automatically deploy an F1-only winner.
No new official-test evaluation is planned; existing test exposure is disclosed. No
independent external dataset is available/claimed. If gate fails, retain original RF/.5.
