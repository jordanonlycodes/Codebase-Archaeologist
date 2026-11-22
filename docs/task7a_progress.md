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


## 3. Focused integration correction

A boundary regression reproduced a genuine convention mismatch: benchmark evaluation
uses probability >= .5, while live classifier argmax returned class0 for a .5 tie.
The new test failed with [0,0,1] versus the recorded-rule [0,1,1]. A localized change in
app/ml/repository.py now derives labels with the shared THRESHOLD, retaining native
shape/class/probability validation. No scores, model bytes, features, splits or metrics
were altered. This affects exact ties only for the deployed binary Random Forest.
Scientific artifacts retain their original checksums; report source hashes remain stale.
Focused post-fix run: **24 passed, 0 failed/skipped** (4 academic-evidence +20 existing
repository-ML cases), one existing warning. Native output safeguards and genuine model
inference remain covered. Current guide now labels Task2-era runtime claims as historical;
tracked vendor documentation now distinguishes optional installation from verified
redistribution. No user-owned vendor asset was staged or modified.


## 4. Final audit artifacts and complete regression

Created the principal eight-requirement/subrequirement matrix, evidence index, original
local demo checklist and machine-readable summary. Classification:1–4,6 PASS;5 PARTIAL
(literal test-each interpretation);7 IMPLEMENTED—not fully browser verified;8 PARTIAL;
group HUMAN CONFIRMATION REQUIRED. No demonstrated P0. P1 closures are human signoff,
portable trusted artifact setup and actual demo;7C report freshness and7D vendor review
remain explicit, with no academic report/source manifest bypass.

Final full suite after correction: **506 passed,0 failed,0 skipped in87.43s**, one existing
Starlette/httpx warning. Four new academic tests passed; focused academic+repository tests
24 passed. Preserved frontend runners cover77 real-document,8 history utility,16 store,
24 graph,10 architecture,32 impact and30 Jordan cases; not added to Python totals.
The updated read-only evidence tool passed, including actual training scale statistics
and all candidate pipeline digests. Dependency check passed. The separate report-source
validator remains FAILED as documented; the pre-fix boundary regression was intentionally
red before correction. Neither failure is hidden in the final green pytest count.

Current environment checks: Chromium exited133 before rendering at setsockopt; Uvicorn
completed startup but failed localhost bind (exit3); direct api.github.com probe failed
DNS (curl6). Independent npm archive re-verification also failed DNS. No live browser,
GitHub, new screenshot, performance measurement or instructor approval is claimed.
Only three existing saved EDA PNGs were visually opened, not a full website acceptance.

Next:7B real local browser acceptance and genuine demo; obtain group/evaluation wording
signoff in parallel before final academic submission;7C final report/evidence refresh;
7D portable trusted model/environment/vendor packaging and remote verification. Task8
viva preparation and optional6C work are not started. Normal safe push follows the final
artifact commit; retain commits and use git push origin main if DNS remains unavailable.
Final static review passed: all audit/doc links resolve, summary has8 main requirements
and32 subrequirement/group rows, Python3.10 grammar and pip consistency pass, diff has no
whitespace errors, and intended changes pass path/size/credential-pattern checks. Original
vendor bundle digest remains unchanged. Current report binaries, ML artifacts, raw data,
existing result metrics and frontend design were not regenerated or modified.
