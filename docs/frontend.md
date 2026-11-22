# Product frontend and workspace lifecycle — Task 5

## Real pages, shared evidence

FastAPI/Jinja renders a public landing (`/`), repository import (`/explore`), and
seven independent `/workspace/` documents: `overview`, `risk`, `structure`, `graph`,
`architecture`, `heatmaps`, `blast-radius`. Unknown workspace names return 404.
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
