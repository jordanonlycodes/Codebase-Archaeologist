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
No training, held-out evaluation, report generation, provider setup or UI redesign is
being performed. Baseline full tests running with the documented process-local polling
selector workaround required by this sandbox.

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
