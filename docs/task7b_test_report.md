# Task7B — application verification report

## Result and evidence boundary

Implementation and automated verification are complete; browser/GPU/responsive acceptance
is **PARTIAL** because this environment cannot launch Chromium or bind localhost.
No known critical runtime defect remains in the exercised backend/harness workflows.
This is not an unconditional human-reviewed university-demo signoff. Team must execute
[the local checklist](task7b_manual_demo_checklist.md) before presentation/capture.

Baseline: **506 passed,0 failed,0 skipped in89.13s**, one existing Starlette/httpx warning.
Final full result is recorded in the final verification section below.

## Test matrix

PASS means the stated automated/API contract was exercised, not that an unavailable
browser visually passed. PARTIAL explicitly reserves human interaction/visual acceptance.

| Area | Status | Evidence and limits |
|---|---|---|
| ZIP ingestion | PASS | tests/test_archive.py,test_api.py; mixed/nested source, invalid/empty/oversized, duplicate/conflicting paths, traversal, links, compression/encryption, CRC, cleanup and no code execution. Fresh mixed ZIP API smoke also passed. |
| GitHub ingestion | PARTIAL | tests/test_github.py mocks actual transport/archives: shared model pipeline, URL allowlist, redirects,404/rate limits/network/timeout/size and SHA provenance. Live DNS blocked, so no real public download claimed. |
| C-model inference | PASS | tests/ml/test_repository.py +test_academic_evidence.py, actual local selected artifact and fresh original demo; invalid/missing artifacts, malformed source, output validation, sanitized inference failure, feature order and inclusive0.5 tie covered. No new benchmark training/evaluation. |
| Overview | PARTIAL | tests/test_product.py actual rendered documents+Node controller hydration/counts/filter/export/navigation;11 public/workspace routes200 in fresh API smoke. Browser composition unverified. |
| Structure | PARTIAL | test_structural.py metrics/malformed/bounds/IDs and real-document frontend harness; C/Python coverage preserved. Browser table/selection visuals unverified. |
| Risk | PARTIAL | Actual3C scores, unscored Python, unchanged model/metrics and real-document search/filter/details/export tests. Browser charts/formatting unverified. |
| Knowledge Graph2D | PARTIAL |25 graph Node cases include shared filters/search/perspectives/layouts/SCC/cycle/directions, safe labels and SVG reuse/drag scheduling/cleanup. Browser pointer/label appearance unverified. |
| Knowledge Graph3D | PARTIAL | Actual adapter executed against instrumented library double: coordinate fit, translated/disconnected/single/empty data, aspect/hidden resize, pan toggle, supported control configuration, scoped keys/events, reset without relayout, quality/MSAA and cleanup. No real WebGL rendering/camera acceptance/FPS claim. |
| Architecture | PARTIAL | test_architecture.py +10 frontend cases and document harness: real components/membership/aggregates/evidence/SCC/bounds. Actual canvas composition unverified. |
| Heatmaps | PARTIAL | Same architecture suites cover six real metric definitions, aggregation, nested drill-down, zero/missing/unscored states and cross-navigation. Visual treemap acceptance pending. |
| Blast Radius | PARTIAL | test_impact.py +32 frontend cases: reverse callers/forward dependencies, membership-only structural edges, depths1–3, paths/cycles/bounds and navigation. Fresh Jordan impact query reproduces actual call edge. Visual layout pending. |
| Jordan Local | PASS |30 frontend local/retrieval cases plus actual mixed-analysis overview/complexity/callers/impact queries. Responses contain real stable IDs; structural evidence only. Browser conversation presentation pending. |
| Jordan mode/error/privacy | PASS | Existing Jordan backend/product harness regressions cover configured/unconfigured/unavailable/error selection and per-request consent. Fresh capabilities: local true, cloud unavailable (disabled/missing key/model). No provider configured or contacted. |
| Time Machine | PARTIAL | test_history.py creates genuine deterministic Git repositories (not invented commits); timeline/activity/churn/compare/tree/evolution Node/document suites. ZIP no-history, pinned revisions and partial trees preserved. Browser/live public history unverified. |
| GitHub API reliability | PASS | test_history_cache.py: TTL/entry/byte/scope isolation, singleflight independence/cancellation/deadlines, public-only gate, token secrecy, primary/secondary/ordinary403/401/404/429/5xx/network/JSON classification and cooldown. Document harness repeated compare/tree/stale cancellation/loaded-state tests retained. Live quota not measured. |
| Exports | PASS | test_api.py, ML integration and document harness assert same source-free response/contracts, browser Blob/name/MIME actions, repeated exports. Actual OS browser download interaction pending. |
| Persistence | PASS |16 store frontend cases and document lifecycle:2h expiry, bounded3×24MiB, per-tab pointers, replacement/failed saves/quota/unavailable storage, refresh/back-forward, stale selections and source-free history. Harness, not actual browser IndexedDB inspection. |
| Responsive UI | PARTIAL | Existing breakpoints/source reviewed; real context-action row lacked wrapping, now wraps <=780px. Workspace lockup compact <=420px. No rendered viewport validation at1440/1366/1024/768/390/320. |
| Accessibility | PARTIAL | Skip links, semantic names/focus/reduced-motion, graph keyboard/browser controls and expanded focus handling retained. Scoped arrow-key pan added; labels/intrinsic dimensions tested. No actual screen-reader/keyboard-trap/contrast certification. Garnet remains ornamental. |
| Branding | PARTIAL |2 new Python tests verify7 local SVGs, safe content/titles, static MIME, PNG and shell references. Actual standalone vector dark/light and16/32/64px previews inspected with librsvg. Not browser/nav/favicons visually certified. |
| Errors/security | PASS | Preserved archive/SSRF/stream/admission/CSP/path/exception protections, safe text rendering, tokens server-only, no cloud consent bypass. Fresh invalid input errors documented below. Security regression evidence is not a penetration-test certification. |

## Actual mixed-language API smoke

Submitted the existing original fixture `tests/fixtures/university_demo/review.c` and
`helpers.py` as a real in-memory ZIP through FastAPI TestClient. This executes the real
extraction, parsers, model and graph/architecture aggregation, without network/browser.

-2 files,24 physical lines,4 structural functions;7 retained graph nodes and7 edges.
- C-only predictions: clamp_index=.6446299251115485 (class1),
  sum_values=.4640631119969904 (class0), entry=.44115041436869545 (class0).
- Python describe_count has complexity2 and no ML score. Highest observed complexity
  is clamp_index3. Scores are unlabeled demonstration outputs, not accuracy evidence.
- Resolved entry→sum_values call. Jordan reports1 direct upstream dependent of
  sum_values,0 transitive at1hop,0 downstream dependencies, with the original edge ID.
- Python-only:1 file/1 structural function/0ML; JS-only:1/0/0ML. Malformed C: partial,
  no invented score. Subsequent API results do not contain previous repository scores.
- Empty ZIP422/empty_repository; invalid ZIP400/invalid_archive;
  traversal400/unsafe_archive; disallowed GitHub URL422/invalid_github_url.
- All11 public/workspace pages returned200. Cloud capabilities were checked only;
  no cloud request was made. Local mode worked without provider credentials.

The ad-hoc smoke initially expected400 for invalid GitHub URLs; the implemented and
existing tested contract is422. Corrected the smoke expectation, not the application.

## 3D findings and regression

Old fit queried asynchronous scene meshes immediately after graphData, and hidden hosts
used800×580 fallback sizing. The adapter now fits bounded retained coordinates using the
actual aspect/FOV, defers hidden sizing and preserves manual camera movement on resize.
Fit requested while hidden resumes after measurement. Reset camera does not erase node
positions. Pan is explicitly enabled with a visible left-drag toggle, right/Ctrl-drag,
viewport-scoped keyboard and existing touch gestures; control events wake idle rendering.
Testing the strengthened adapter harness against the original adapter failed at the new
coordinate-fit assertion. Current harness25/25 passes, including pan-toggle lifecycle.
This establishes source-level regressions; physical camera behavior still needs browser.

## Vendor and portability assessment

The untracked runtime bundle is required only for3D, not2D or analytical APIs. LICENSE
and receipt are attribution/provenance records, not runtime loads. Bundle SHA256 remains
`19b3be27040fc894e56d684d53c5f62526c25e5d27f37e8fe91fafff605e4ef4`, matching its local
receipt. Top-level [v1.73.3 MIT license](https://raw.githubusercontent.com/vasturiano/3d-force-graph/v1.73.3/LICENSE)
matches inspected local text (Vasco Asturiano2017). No embedded license/copyright notices
are present in the minified bundle; receipt dependency ranges are not a resolved license
inventory. Independent npm archive retrieval cannot run here (DNS). **Do not commit these
three files yet.** Task7D should verify archive/digests and preserve complete transitive
notices as one justified distributable set. No files were deleted/staged/modified.

Selected model exists locally (~4.3MiB) but is intentionally ignored. Clean checkout does
not contain it; restore the trusted pipeline+metadata+feature schema and matching versions.
Read-only evidence verification passed all three candidate digests, selected checksum,
cleaning, matrices and train-derived preprocessing; no benchmark retraining. Portability
on a fresh Ubuntu machine is not certified. Details/checksum in manual checklist.

## Environment and deferred issues

- Fresh Chromium exit133, `setsockopt: Operation not permitted`, before any render.
- Uvicorn startup completed, localhost bind127.0.0.1:8000 failed, exit3.
- Direct API GitHub curl failed DNS, exit6. No live download/history/push verification
  follows from web-tool cached documentation lookups. No website screenshots captured.
- Report validator still exits1 on app/ml/repository.py source checksum; six known
  stale paths listed in7C handoff. Report output checksums still match. Not a runtime
  regression or green validator. Academic DOCX/PDF were not regenerated.
- Existing Starlette/httpx warning remains; no unrelated dependency upgrade attempted.
- Optional modules/cloud integration and 3rd-party redistribution remain outside7B.

## Final commands and results

- Full suite with baseline's exact process-local polling wrapper:
  **508 passed,0 failed,0 skipped in96.58s**, one existing Starlette/httpx deprecation.
- `node tests/frontend/graph.test.cjs`: **25 passed**, including new pan lifecycle and
  expanded real-adapter checks. Original adapter against strengthened checks fails;
  this deliberate pre-fix regression is separate from final green results.
- Focused graph/product Python run:25passed/38.47s. Brand/product run:21passed/43.37s.
- Full pytest includes real-document product/history and existing graph, workspace,
  architecture, impact and Jordan Node runners; no npm package install or browser used.
- `node --check` passed all28 non-vendor applicationJSfiles; `python -m pip check`
  passed; `git diff --check` passed. SVG/static routes inspected by new2Python tests.
- `PYTHONPATH=. .venv/bin/python tools/audit_academic_evidence.py`: passed read-only
  evidence invariants. `python tools/validate_report.py`: **failed**, known stale source
  hash; deliberately left for7C. No report validation claim is hidden by pytest passes.

See baseline for exact environment/workaround, manual checklist for ordinary local
commands and acceptance, progress for checkpoint commits and7C handoff for open work.

Remote outcome: normal push failed exit128 (`Could not resolve host: github.com`).
Commits are retained locally; use `git push origin main` when networking works. Original
three untracked vendor files remain unchanged. Independent npm archive verification was
also freshly attempted and failed DNS; this does not undo the local digest match.
