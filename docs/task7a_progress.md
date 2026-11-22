# Task 7A — compliance audit recovery record

## 1. Repository/evidence inventory

Audit starts at `5914361742023560edfd7ffff47a0cf556d39a13` on main. Local HEAD equals
local origin/main; no tracked changes or outgoing commits at entry. This checks the
local remote-tracking reference, not fresh network access. Three user-owned untracked
vendor files remain untouched: pinned 3D bundle, top-level license and receipt.
Authoritative criteria are the exact substantive requirements supplied in Task7A;
the university's original PDF was not independently supplied/opened.

Inspected README, ML guide, acquisition/cleaning/features/training/evaluation/loading
code, tracked result JSON, existing report text/metadata, source manifests and local
artifact inventory. Three candidate pipelines and selected Random Forest exist locally.
No benchmark retraining, held-out evaluation, report generation, provider setup or UI redesign is
being performed. Baseline full tests: **502 passed, 0 failed, 0 skipped** (87.40s); one existing
Starlette/httpx warning. The documented process-local polling selector workaround is
required here. Existing tiny training-row reproducibility test fits are unchanged;
no benchmark experiment was fitted or re-evaluated.

Initial findings to verify: all candidates have train/validation metrics, only selected
RF has final held-out metrics; group approval is a student-supplied claim, no documentary
approval located; report is explicitly Tasks1–3A and stale for the final product; source
raw data/models intentionally ignored; untracked 3D file matches its receipt but bundled
third-party license/provenance needs investigation. Existing reports/ml/README.md has
Task2-era statements saying inference is not integrated, contradicted by current routes.
These are audit findings, not permission to change experimental evidence.

Next: independently verify checksums/schema/cleaning/matrices and saved metric formulas;
run selected-artifact mixed ZIP smoke; validate report structure read-only; inspect EDA
figures/vendor provenance; make only small justified documentation/invariant corrections;
produce matrix, evidence index, demo checklist and optional machine-readable summary;
complete tests and normal push.


## 2. Dataset/preprocessing/model verification complete

Read-only source audit verified all raw/selected completion checksums, actual Parquet
schemas/counts and class counts, reproduced the exact cleaning audit and all113 removal
records, confirmed retained row identities/labels and the 21,750×11 / 2,723×11 matrices,
and matched six extracted development examples to persisted feature rows. Train-derived
median imputation and LR scaling statistics match the saved pipelines. Preparation and
experiment implementation hashes agree. All three candidate checkpoints/metrics and
selected metadata/results agree with tracked evidence. No held-out predictions were run.
The new read-only tools/audit_academic_evidence.py preserves the verification command.

Three narrowly targeted regression tests passed: saved confusion-matrix arithmetic and
selection, feature/cleaning metadata consistency, and genuine selected-artifact inference
on an original mixed C/Python demo fixture. Fixture result: 2 files, 4 structural functions,
3 genuine C predictions, 7 graph nodes. Scores observed: clamp_index .6446299251115485,
sum_values .4640631119969904, entry .44115041436869545. These are unlabeled fixture
predictions, not an accuracy experiment or confirmed defects. Python remains unscored.
Separate in-process checks verified Python-only/unsupported, malformed C, empty/invalid
ZIP, missing model and inference-failure states without disabling static analysis.

Existing report: read-only XML/PDF checks verified 28 pages, 5707 DOCX words, 9 images,
19 sections, correct identity and exact saved metrics; output hashes match. The original
report validator **fails**, first at changed app/ml/repository.py source hash. Six source
manifest paths are stale/missing after later tasks. Do not bypass or update its success
record now; refresh the report/evidence manifest in Task7C. Plot labels were visually
inspected on three actual saved EDA figures, not on a running application.

The 3D bundle hash matches its local receipt; top-level MIT text matches upstream license.
Independent npm archive re-verification failed DNS. The bundle contains no embedded MIT,
Copyright or license notices; exact transitive versions are not pinned by the receipt's
ranges. Leave all three user-owned files untracked; recommend vendoring as one reviewed
set only after archive integrity and third-party notices are completed for Task7D.
