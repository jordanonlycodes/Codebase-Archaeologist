# Product frontend and workspace lifecycle — Task 5

## Real pages, shared evidence

FastAPI/Jinja renders a public landing (`/`), repository import (`/explore`), and
eight independent `/workspace/` documents: `overview`, `risk`, `structure`, `graph`,
`architecture`, `heatmaps`, `blast-radius`, `jordan`. Unknown workspace names return 404.
`workspace_base.html` owns one navigation/context shell; validated feature includes
contain only that page's relevant controls and content. Architecture and heatmaps
share an engine/template but initialize different actual views. They do not load a
hidden massive dashboard. The superseded dashboard template, CSS and controller
have been removed.

`product/design.css` owns shared tokens, typography, layout and primitives; page styles
and the existing scoped visualization modules own feature presentation. Noto Sans and
Noto Serif Display subsets are served locally with the SIL OFL attribution/license.
No remote fonts, framework, bundler or new runtime dependency is required.

`product/common.js` supplies small display helpers, the workspace store and whitelisted
navigation. `product/workspace.js` restores a snapshot once and hydrates only the active
feature. `product/import.js` is the only new controller issuing analysis requests.
Existing analytical response fields and engines remain unchanged.

## State and retention

`product/store.js` stores the **source-free analysis response** in IndexedDB. Raw ZIPs,
extracted code and dataset/model artifacts are never added to browser storage. A per-tab
`sessionStorage` opaque pointer selects that tab's active snapshot; payloads are never
placed in URLs, cookies, localStorage or server-global mutable state. This is local
browser-profile isolation, not authentication or encrypted storage. Same-origin scripts
and anyone with access to the browser profile can inspect retained data. Do not analyze
sensitive repositories on a shared browser profile.

Policy: two hours from save, at most 24 MiB compact UTF-8 JSON per snapshot and three
snapshots per origin. Opening a fourth context can evict an older tab's snapshot.
Expiration is enforced when restoring and by an active-page timer; expired records are
physically pruned on the next application storage operation. Browsers may throttle
background timers. Forget snapshot deletes the active payload and tab preferences.
A new successful analysis replaces the tab pointer and clears stale feature selections.
Failed analysis/storage leaves the prior pointer unchanged; failed pointer persistence
rolls back the new payload. Import offers unsaved JSON export if persistence is blocked.
No account, bearer snapshot URL or shared server repository store is introduced.

IndexedDB uses separate small metadata and payload stores. Retention pruning inspects
metadata rather than loading all retained analysis payloads on every navigation. A
transaction bounds snapshot writes; payload restoration reads only the active record.
UI preferences are capped at 32 KiB. There is no second large payload in synchronous
storage. No backend analysis runs merely because the user navigates.

## Navigation and lifecycle

Standard anchors/document navigation preserve native back/forward and deep links.
A direct workspace load or refresh restores the tab's snapshot, or presents an intentional
empty/error state. Cross-feature handoffs carry `{page,id}` in small per-tab state,
consumed once after hydration. Graph/structural/component IDs are reused; function
source names are never used as navigation identity. The current page captures relevant
filters/selection before leaving. Graph collapsed-group state is capped to 100 IDs.

Only the graph page loads 2D/3D adapter code; the actual pinned 3D bundle is still lazy-
loaded on demand. Architecture/heatmaps and impact reuse the bounded event-driven SVG
viewport. `pagehide` disposes active renderer/scene resources. A back/forward cache
restoration recreates the renderer, without registering a second set of control listeners;
if its snapshot pointer changed or expired, it reloads the correct page context.

ZIP progress measures actual transferred bytes only. Once transfer finishes, analysis
is explicitly indeterminate; GitHub downloading/analysis is also indeterminate. No
stage percentages or fake repository previews are generated. Cancellation aborts the
client request; server cleanup still follows the original request lifecycle.

## Verification

Baseline before redesign: 385 passing Python tests. The initial integrated page migration
passed **399 Python tests** including **19 real-document browser-free integration cases**,
10 store lifecycle cases, and all existing graph/architecture/impact suites. Existing
regression assertions were moved to their appropriate dedicated routes; analytical,
export, security and model assertions were retained. Later refinement verification is
recorded in `task5_progress.md` and the final README.

The document harness consumes actual FastAPI HTML and a real mixed C/Python analysis
response. It checks strict element lookup, feature boot, real counts, empty states,
ID-based cross-page handoffs, ZIP/GitHub submission, indeterminate processing state,
no navigation-time analysis, graph teardown/history restoration and storage failures.
It is not a browser, visual layout test or real GPU/WebGL verification.

Chromium was attempted again and failed at startup with `setsockopt: Operation not
permitted` (exit 133). No authentic application screenshots or measured FPS are claimed.
Run `pytest tests/test_product.py -q -s` for the document integration suite. Browser
verification instructions and final design review will be maintained here as later
Task 5 stages are completed. Academic PDF/DOCX files remain unchanged.

## Visualization refinement

The dedicated graph stylesheet was rebuilt rather than layered over legacy rules.
Controls use neutral compact surfaces, coverage/graphics detail is collapsible, labels
retain contextual collision rules, and inspectors use readable text with scrolling
identifiers. Existing perspective layouts, bounds and all six 2D/3D/perspective
combinations remain covered by graph regression fixtures.

Architecture now assigns deterministic separate curve lanes to parallel and reverse
component relationships; no source edges are changed. Heatmap non-ML metrics use a
muted warm scale; hotspot/model-score metrics use garnet, missing remains hatched and
actual zero remains neutral. Component selection preserves geometry. Impact retains
its anchored, direction-specific layout and evidence trails with coordinated neutral
surfaces. File/component cross-navigation uses indexed stable memberships.

3D reuses its existing sphere materials for restrained emissive color (intensity .12),
without extra geometry, lights or postprocessing. Performance/adaptive-reduced mode
sets that emission to zero. MSAA remains unrequested in all modes; pixel ratio, normal
label count, low geometry resolution and idle pause policies remain intact. These
behaviors were checked through the adapter fixture, not a real GPU profile.

Font assets now use local WOFF (256,404 bytes total versus 480,320 bytes for the initial
TTF subsets); primary interface and landing editorial faces are preloaded. No measured
CLS, FPS or visual smoothness claim is made. Firefox was also attempted and exited 139
before rendering. Focused refinement verification: **27 Python checks passed**, including
**21 document-journey cases**, graph (24), architecture (10), impact (32) and store (10)
Node cases through their respective runners. A final full suite follows Stage H.

## Signature README and assets

`docs/assets/hero.svg` is original brand artwork, not an application screenshot. It
shares the website's graphite/ivory, italic editorial typography and organic light motif.
`tools/generate_brand_assets.py` converts the tracked OFL font outlines to SVG paths,
so GitHub needs no remote fonts, scripts, foreign objects or raster assets. Local XML
validation, deterministic regeneration and a real `rsvg-convert` render were checked;
the resulting brand PNG was visually inspected. This verifies the brand asset only,
not website rendering. The warm layered product mark replaces the original cyan icon.

Authentic screenshots remain pending. `docs/screenshots/README.md` provides the exact
capture workflow and prohibits substituting mockups. The redesigned README documents
real routes, snapshot retention, installation, preserved capabilities and exact saved
validation/test metrics, with scientific caveats and separate dataset/font/vendor licensing.
Stage G checks: 16 product tests passed; brand XML, reproducibility and local links passed.

## Final Task 5 quality and verification record

Final regression run: **402 Python tests passed, 0 failed, 0 skipped**, with one existing
Starlette/httpx deprecation warning. Browser-free frontend suites cover **29 real-document
journey cases**, **14 store/IndexedDB API-harness cases**, **24 graph cases**, **10
architecture cases** and **32 impact cases**, plus the original real-response impact
smoke check with and without the trusted artifact. Node cases are exercised by Python
runners and are not added to the Python total. JavaScript syntax checks, Python compile,
`pip check`, all local documentation links, stylesheet block balance, SVG XML and
brand-asset deterministic regeneration passed. The preserved 3D bundle matches its
existing receipt. No raw dataset, model artifact or academic report was changed.

The final engineering/design review checked:

- Single feature documents, active navigation, semantic headings and functioning entry
  points; compact mobile public navigation and a serif/sans-serif identity throughout.
- Real API values in overview/risk/structure, Python-only usefulness, no fabricated scores,
  and exact saved experiment metrics in README.
- Stable-ID graph/component/file/impact handoffs and filter/selection restoration.
- Saved 2D preference applied before automatic 3D initialization; unsupported saved 3D
  consistently falls back to 2D. Only one adapter attaches, including async load races.
- No renderer resurrection from late visibility events after pagehide; restoration during
  navigation is ignored by the retired document. Idle IndexedDB connections close and
  reopen lazily. Back/forward restoration recreates rendering without analysis.
- Fullscreen fallback has dialog semantics, focus entry, Tab boundaries and Escape/trigger
  focus restoration. Mobile navigation has visible focus and Escape handling.
- Source paths/identifiers remain accessible through inspection/scrolling; rendered labels
  are bounded/contextual. Partial analysis, empty state and unscored values remain explicit.
- Invalid replacement files clear pending input. Storage failure preserves the old context
  and offers real unsaved JSON, never a false successful redirect.
- Reduced motion, offscreen/hidden landing suspension, conservative canvas resolution,
  deterministic graph geometry and performance-profile effects limitations.

These are source, integration and fixture checks, not a rendered visual acceptance test.
The SVG brand artwork alone was rendered and visually inspected. Uvicorn imported,
completed startup, then failed to bind `127.0.0.1:8000` here. Chromium exited 133 with
`setsockopt: Operation not permitted`; Firefox exited 139 before rendering. Website
screenshots, actual 1366×768/mobile visual inspection, real WebGL appearance, console
verification and performance traces remain outstanding. No FPS, CLS, smoothness or
visual-success claims are inferred from the mocks.

Product HTML keeps the self-only CSP. FastAPI's pre-existing Swagger/ReDoc pages retain
their framework CDN defaults so the redesign does not break their scripts; those reference
UIs need network, while `/openapi.json` and installed product assets remain local.

### Local visual acceptance

1. Follow README setup and start Uvicorn on localhost. Open `/` at 1366×768; inspect the
   still composition, motion, scroll narrative and immediate import access. Repeat with
   reduced motion and narrow widths (390×844, tablet and large desktop).
2. Import a known mixed C/Python ZIP, then navigate all eight workspaces without a
   second upload. Refresh each and exercise browser back/forward. Open a new tab to
   verify its context behavior; remember browser tab duplication may copy sessionStorage.
3. Inspect overview provenance and inventory filters; select actual functions in structure
   and risk, then navigate their graph/impact evidence. Test a Python-only repository.
4. In graph: test 2D and genuine WebGL 3D, all perspectives, quality profiles, overlays,
   search, selected/hover labels, zoom/drag, expanded view focus and reduced motion.
   Record performance traces on the Intel HD 620 before claiming improvements.
5. In architecture: inspect parallel/reverse arrows, source evidence, components/cycles.
   In heatmaps: all six metrics, drill-down, breadcrumbs, missing vs zero vs unscored.
6. In impact: one/two/three hops, upstream/downstream/both, off-canvas results and complete
   path inspection. Compare arrows and source lines manually against the fixture.
7. Export from each page; from impact, confirm the current query is included. Replace
   the repository, forget it, test expiry/storage denial and malformed GitHub/ZIP inputs.
8. Check console errors, long paths, keyboard flow and screenshots using
   [the authentic screenshot checklist](screenshots/README.md). Only commit actual captures.


## Jordan extension — Task 6A

`/workspace/jordan` loads only the existing impact engine and scoped retrieval, local
intelligence and conversation modules. It builds one snapshot-local index and uses
retained stable IDs, not source parsing. Normal navigation still does not reanalyze.
`WorkspaceNavigation.askJordan` stores a compact validated entity reference, source page,
suggested question and optional exact impact target/depth/direction in the existing
one-shot handoff. Unknown identities are rejected. The evidence inspector navigates
back into real graph, structure, architecture and impact workspaces.

The per-snapshot Jordan preference contains at most eight local turns / 18 KiB within
the shared 32 KiB preferences cap. Cloud replies remain in page memory and are never
persisted. Replacement/forget/expiry clears conversation context; expired or absent
active pointers now also remove leftover conversation/preferences. Pagehide aborts
capability/provider requests, clears disclosure and drops indexes. Epoch checks reject
late answers. History restoration reconstructs indexes without duplicated listeners.
The native details panels collapse at smaller widths; no rendering loop or dependency
was added. Safe textContent rendering handles user, repository and generated text.

Only explicit reviewed cloud requests cross the API boundary with selected facts. There
is no server snapshot mirror or global assistant state. See [Jordan](jordan.md) for the
provider trust boundary, disclosure, configuration and complete verification record.


Task 6A final regression record: **435 Python tests passed, zero failed/skipped**, with
one existing Starlette/httpx warning. The browser-free document suite now has 44 cases,
Jordan utilities 30 and snapshot persistence 15. Existing graph (24), architecture (10)
and impact (32) suites remain green. These counts are not added to the Python total.
Mixed C/Python real-ingestion smoke: 3 files, 4 structural functions, 2 actual C-model
predictions; verified local caller and impact answers. Uvicorn reached application
startup but could not bind localhost. Chromium again exited 133 at setsockopt; Firefox
exited 139 before rendering. Jordan visual/responsive acceptance and live cloud testing
remain local manual checks in jordan.md; no measured FPS or screenshots are claimed.
