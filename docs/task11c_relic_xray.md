# Task 11C — RELIC // X-RAY

## Baseline and protected release

Work began on `feature/cinematic-experience` at
`42958fb47027ec8091388206f4a2a9eb18a7ca0b`, with a clean working tree.
The annotated `v1.0.0-university-release` tag still resolves to
`09f6b6df29b6b3e8e81c48c7f8f929a6e638dce5`; `main` is preserved.
No model, brand asset, academic report or submission archive is changed.

Fresh baseline: `.venv/bin/python -m pytest -q` — **553 passed**, no failures
or skips, one existing Starlette/httpx deprecation warning, 16.87 seconds.
The prior Universe design and approved rounded controls remain in place.

## Architecture and actual evidence

X-Ray is a projection of the existing source-free analysis snapshot, not another
analyzer or an independent graph. It makes no network requests and adds no
runtime dependencies. The only server change registers its local CSS/JS assets
on the existing Knowledge Explorer route.

Evidence of record:

| Source | Contract used |
|---|---|
| `app/analysis/graph/engine.py::extract_graph` | Real repository, directory, file and analyzed-function nodes; `CONTAINS` and `DEFINES` ownership; C-only prediction linkage |
| `app/analysis/graph/models.py` | Stable node/edge IDs, typed relationships and source evidence locations |
| `app/static/graph/data.js::index` | Canonical node map, valid resolved internal edges, incoming/outgoing maps, ownership hierarchy and unresolved/external references |
| `app/static/graph/explorer.js` | Existing selection, renderer lifecycle, Universe camera focus and inspector |
| `app/static/product/workspace.js` | Active bounded snapshot, expiration, repository handoff and page lifecycle |
| `app/static/graph/xray.js` | Derived hierarchy, navigation history, direct tracing, risk scope and X-Ray controller |

Function metadata contains language, ownership path, source lines, structural
counts and, for eligible C functions, the existing `metadata.ml` result. It does
not expose a model explanation or full source bodies. X-Ray invents neither.
Its structural measurements are not relabeled as the model's feature vector or
as a causal explanation for a score.

## Investigation workspace

Knowledge Explorer has a visible **Activate X-Ray** entry. Universe's selected
entity inspector also offers **Inspect in X-Ray** for real directories, files
and functions. The workspace identifies itself as **RELIC // X-RAY**, with
**X-RAY MODE ACTIVE**, **SEE BENEATH THE STRUCTURE**, and an obvious **Exit X-Ray**.

The graphite/ivory/garnet cross-section contains three persistent plates:

1. **01 / STRUCTURE:** immediate child directories of the selected directory,
   or top-level directories at the repository overview.
2. **02 / FILE SYSTEM:** files directly owned by that directory. Selecting one
   reveals its retained definitions in the function plate.
3. **03 / FUNCTION INTELLIGENCE:** actual function definitions owned by the
   selected file. Selection updates the evidence inspector.

Nested directories drill down through the same structure plate. Breadcrumbs
include every retained ownership ancestor, not just the last path segment.
Directory summaries count retained descendant files/functions, including nested
directories. They do not count cross-file calls as ownership. The directory
counts remain exact above 6,000 nodes; the source graph already has explicit
server bounds of 12,000 nodes / 20,000 edges.

An active plate has both `aria-current="step"` and a textual stage status.
Selected entity cards include **SELECTED**, rather than relying only on color.
The view is intentionally not a claim of inferred runtime module boundaries.

## Entity identity and navigation

All actionable entity IDs are existing canonical graph IDs. No synthetic
directory, function, grouping anchor or dependency is added. Root overview is a
null presentation selection, not a new graph entity. Unowned retained files or
functions remain accessible at root; ownership is not guessed from names.

`graphExplorer.state.selected` is the shared selection authority. X-Ray keeps
only bounded presentation history: at most 40 stable IDs with a cursor.
Back/Forward restore selections; branching truncates the forward history.
Return to Structure, Clear Selection and the repository breadcrumb return to
overview. Unknown IDs produce an explanation while retaining successful data.

Universe → X-Ray passes the exact ID. X-Ray → **Locate in Universe** uses the
existing `choose` and `focusEntity` methods, including neighborhood/filter
handling. Returning without Locate refreshes the original renderer with the
shared selection. The existing renderer is reused when available, with no
second canvas. Pending renderer initialization is invalidated on activation;
an existing renderer's context-loss guard remains valid.

`Explorer.setGraph` resets X-Ray before replacing the canonical index: mode,
history, selection, animations and old inspector evidence are cleared. Saved
graph preferences retain their existing bounded contract; X-Ray does not persist
another snapshot, source body or duplicate graph.

## RELIC // EVIDENCE and tracing

Directory evidence: path, retained descendant file/function counts and direct
child directory count. File evidence: path, language and owned function count.
Function evidence: name, owning file, source lines, complexity, nesting and
parameter counts when provided. Identity and measurements use a native
expandable disclosure; missing fields remain **Unavailable**.

**Trace Dependencies** lists incoming/outgoing **direct** canonical edges.
Each row preserves the relationship type, direction, related entity and up to
three source evidence locations when present. Related-entity buttons continue
the investigation at that exact entity. Direction buttons filter the same edge
set; Clear tracing removes it without changing analysis.

`CONTAINS` and `DEFINES` are labeled **Structural ownership**. `CALLS`, `IMPORTS`
and `INCLUDES` retain their actual type and are labeled **Static dependency**.
No transitive paths are computed or presented as direct evidence. Unknown or
external references are not internal edges: their retained count is explained,
with Universe/JSON export identified for full reference details. At most 40
direct edge rows are shown, with an explicit remainder notice.

## C-only risk scope

The inspector displays the existing score only for a function with language C,
`ml.status === 'analyzed'`, a valid binary predicted class and a finite numeric
score in [0,1]. Zero remains a valid score; null, strings, NaN, infinity and
out-of-range values remain unavailable. Python is explicitly described as
outside C-model inference, even if inappropriate ML metadata were supplied.

The unchanged production model is Random Forest `devign-v1-4a23cc304ca8`, with
11 original features and threshold **score ≥ 0.5**. X-Ray neither loads a model
nor recomputes a probability. The score is labeled a C-function defect-risk
research estimate, uncalibrated, not a confirmed defect or vulnerability. A
predicted class is read from evidence, not reclassified in the frontend.

## Motion, performance and accessibility

- Activation uses a finite 650 ms opacity/12 px rise. Drill-down uses a finite
  320 ms opacity/6 px rise, with the established restrained easing.
- Inactive plates use a subtle fixed depth transform; active plates remain
  prominent. No continuous effects, artificial processing or loading delays.
- At most one owned WAAPI animation survives navigation. Replacement, exit,
  repository reset, document hiding and pagehide cancel it. Completion releases
  its reference. Reduced-motion changes cancel immediately, and future reveals
  show final content without animation; CSS removes depth transforms.
- The hidden 3D renderer pauses, including its camera animation. X-Ray does not
  restart physics, initialize another renderer or fetch data. Existing
  intersection/visibility lifecycle resumes it when visible again. BFCache
  restoration respects the X-Ray guard on renderer startup.
- Each plate renders at most 36 entity cards with native Previous/Next controls;
  history is capped at 40 entries and evidence rows at 40. Traversals are
  cycle-safe over the already bounded graph; no recursive DOM tree is built.
- Listeners are installed once per document, not on each drill-down. There are
  no X-Ray timers, observers or animation-frame loops. Document lifecycle
  handlers remain available for BFCache restoration.
- Native buttons, breadcrumb navigation, visible shared focus rings,
  `aria-pressed`, polite status text and non-color selected states are used.
  Focus moves to the selected card or heading on drill-down and returns to the
  opening control on exit. Escape first clears a trace, then exits. There is no
  modal focus trap or unsafe HTML insertion.
- A stacked inspector below 1100 px avoids covering navigation. Long paths
  wrap, mobile primary controls are at least 44 px, and shared radius tokens
  preserve Task 11B controls. Essential content is never CSS-hidden pending
  animation. Initialization failure leaves the normal Universe available;
  guarded interaction failures exit X-Ray with a recoverable explanation.

## Verification

Primary automated evidence:

- `tests/frontend/xray.test.cjs`: hierarchy, deterministic IDs, nested/direct
  ownership, cycles/orphans, large exact counts, tracing/direction/type, C-only
  risk validation, zero values, empty graphs and bounded history.
- Twelve added real-document cases in `tests/frontend/product.test.cjs`: shared
  snapshot/selection, drill-down, Back/Forward, traces, Python scope, handoffs,
  reset invalidation, empty states, reduced motion, animation cancellation,
  pending renderer cancellation and BFCache restoration.
- `tests/test_xray.py`: Node contract wrapper, actual route/static assets,
  semantic controls, no-fetch/no-innerHTML contract and lazy page isolation.

Fresh final regression and browser receipts are recorded below in the release
closure section. Browser checks use real server analysis of original project
fixtures; they do not intercept analysis responses or invent source entities.

### Chromium evidence

`tools/task11c_browser.mjs` records real Chromium 157.0.8103.79 results in
`reports/ui/task11c/browser.json`, including source hashes, input ZIP hash,
timestamp, viewport widths and individual assertions. The five-file mixed-source
fixture from `tools/create_xray_acceptance_fixture.py` includes three eligible
C functions, Python functions, a functionless deeply nested Python file with a
long directory name, and a root Markdown file.

Checks include all three levels, directory counts, function scores, Python
exclusion, direct CALLS navigation, breadcrumbs, history, invalid-ID recovery,
Escape, actual keyboard Enter, visible focus, reduced-motion changes, renderer
pause/reuse, tour cancellation, Universe handoffs, empty state, rapid selection,
no new API requests, no uncaught script exceptions and all four viewport widths.
The explicit null-graph check is a presentation failure fixture, not a claim
that the analyzer returned an empty graph for the mixed source.

Genuine viewport captures, visually inspected:

| Capture | Evidence |
|---|---|
| `reports/ui/task11c/overview.png` | Repository directories and root file |
| `reports/ui/task11c/directory.png` | Directory investigation and direct file plate |
| `reports/ui/task11c/file.png` | Actual C file and its function definitions |
| `reports/ui/task11c/function.png` | Selected C function and saved risk estimate |
| `reports/ui/task11c/dependency-trace.png` | Real `entry → sum_values` CALLS edge, ownership separately labeled |
| `reports/ui/task11c/mobile.png` | 390 px navigation and stacked structural plates |
| `reports/ui/task11c/mobile-investigation.png` | 390 px evidence inspector |

## Reproduce and demonstrate

From the repository root:

```bash
source .venv/bin/activate
python tools/create_xray_acceptance_fixture.py /tmp/task11c-demo.zip
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Use the project's README for clean installation/model prerequisites. Open
`http://127.0.0.1:8000/explore` and upload `/tmp/task11c-demo.zip`. Open Knowledge
explorer, then **Activate X-Ray**. Select **src**, **review.c**, **entry**.
Expand **Identity & structural measurements**, then **Trace Dependencies**.
Point out the actual outgoing CALLS target **sum_values** and incoming DEFINES
ownership. Select the target, use Back, and **Locate in Universe**. In the
Universe inspector, select **Inspect in X-Ray**. Investigate a Python function
to show its explicit scope limitation. Exit using Escape or Exit X-Ray.

For isolated browser acceptance, use a separate server/profile (do not reuse
the user's active browser profile):

```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8015 --no-access-log
chromium --headless --disable-extensions --remote-debugging-port=9228 \
  --user-data-dir=/tmp/codebase-task11c-chromium --window-size=1440,1100 about:blank
# In another terminal, with both processes running:
BASE_URL=http://127.0.0.1:8015 CHROME_DEBUG_URL=http://127.0.0.1:9228 \
  DEMO_ZIP=/tmp/task11c-demo.zip node tools/task11c_browser.mjs
```

No browser sandbox protections are disabled. Actual captures are browser output,
not generated mockups. The normal host application on port 8000 is untouched.
After updating the route's asset list, an existing non-reloading application
process needs a normal restart to serve the new script/style references.

## Known limits and Task 11D handoff

Architecture and counts cover retained static evidence, not all possible
runtime behavior. No transitive tracing, source preview or fabricated model
explanation is introduced. A truncated source graph cannot prove independence.
Missing ownership is explicit. A corrupt ownership cycle is bounded and not
treated as a valid repository hierarchy.

Chromium uses the host's headless WebGL stack; this is not physical touchscreen,
hardware FPS, full assistive-technology or WCAG certification. Existing
third-party stylesheet injection can produce CSP console policy warnings;
the local fallback CSS and unchanged CSP remain in place. No uncaught script
exceptions are accepted as passing.

The university report and release remain frozen at Task 7E. The academic source
manifest is therefore checked against its immutable release commit, not
misrepresented as evidence of the newer cinematic feature. New X-Ray captures
are development evidence; academic documents are not regenerated in this task.

Task 11D can build on the shared canonical selection and these tested controls.
It must preserve C-only inference, source bounds, offline rendering, reduced
motion and the unchanged university release.

## Release closure — 23 November 2026

| Validation | Actual result |
|---|---|
| `.venv/bin/python -m pytest -q` | **556 passed**, zero failed/skipped; 18.01 s; one pre-existing Starlette/httpx warning |
| `node --test tests/frontend/*.test.cjs` with the pytest-produced `PRODUCT_FIXTURE` | **276 passed**, zero failed/skipped (172 standalone + 96 real-document + 8 history cases) |
| `node --check` over non-vendor application scripts | **32 passed**; both changed browser tools also pass |
| `node tools/task11c_browser.mjs` | **52 Chromium checks passed**, four widths, seven genuine captures |
| Existing `tools/task11b_browser.mjs`, isolated output directory | **83 Chromium checks passed** against the new implementation |
| `tools/verify_vendor_assets.py` | Approved offline bundle and provenance receipt still match |
| `tools/validate_report.py --source-ref 09f6b6df29b6b3e8e81c48c7f8f929a6e638dce5` | Frozen report validation passes, read-only; no report regeneration |
| `tools/check_report_links.py` | 61 local links/figures checked, none missing |
| Browser receipt source hash comparison | All tested application source hashes still match |
| `git diff --check` | Pass |

The frontend fixture is created by
`tests/test_product.py::test_real_documents_boot_with_shared_analysis_and_cross_page_navigation`;
it supplies actual API-produced snapshots and local Git-history evidence to the
Node harness. The Python count includes wrappers that execute these Node tests;
the counts represent different test layers and should not be added together as
independent Python tests.

Universe regression receipts/captures are in
`reports/ui/task11c/universe-regression/`; prior Task 11B evidence was not
overwritten. To rerun that suite:

```bash
python tools/create_acceptance_fixture.py /tmp/task11c-universe-demo.zip
BASE_URL=http://127.0.0.1:8015 CHROME_DEBUG_URL=http://127.0.0.1:9228 \
  DEMO_ZIP=/tmp/task11c-universe-demo.zip \
  ACCEPTANCE_OUTPUT=reports/ui/task11c/universe-regression \
  node tools/task11b_browser.mjs
```

Browser harness bring-up required three tooling corrections: avoid serializing
the circular WebGL adapter as a CDP return value, send the Enter keypress text,
and restore normal motion before expecting timed tour playback. Those were
verification-tool issues, not suppressed application failures. Screenshot
inspection prompted a genuine inspector layout improvement: C risk now appears
before the expandable measurements. No tests or assertions were removed.

There are no known critical application defects from these checks. Physical
device/GPU and full screen-reader acceptance retain the limitations above.

Implementation checkpoint: `728d4fc` — Build Relic X-Ray architecture
investigation on canonical graph evidence. The acceptance checkpoint adds
browser tooling and receipts separately. `reports/ui/task11c/verification.json`
records the tested implementation commit, counts and SHA-256/provenance for all
seven X-Ray captures. Browser receipts also bind the tests to application source
hashes. The final Git commit is obtained with `git rev-parse HEAD` rather than
embedding a self-referential commit ID in this document.
