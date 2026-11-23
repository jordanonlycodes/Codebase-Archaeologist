# Task 11D — RELIC // LIVE

## Scope and preserved baseline

Development branch: `feature/cinematic-experience`. Initial clean HEAD:
`a0a8af409ab73ba89d9d6f7594ab6b3573e36dc8`.
`main` and `v1.0.0-university-release` remain at
`09f6b6df29b6b3e8e81c48c7f8f929a6e638dce5`.
No model, training, academic report, submission archive or vendor asset changed.
Fresh baseline: **556 Python tests passed**, no failures/skips, one existing
Starlette/httpx deprecation warning, 17.40 seconds.

## Architecture and sources

`/live` is a dedicated Jinja2 document with pre-flight and an immersive viewport
shell. Links appear in the existing public and workspace navigation. It loads
the existing store, motion/statistics utilities, graph/X-Ray and Time Machine
assets, then `product/live.js`. It deliberately does not load the ordinary
workspace hydration controller, which would initialize a competing lifecycle.
There is no iframe, second graph renderer, second X-Ray engine or new dependency.
The existing CSP remains intact.

One canonical `workspaceStore.load()` snapshot supplies all scenes. The real
`knowledge-explorer` DOM node moves between the Universe and X-Ray slots; its
controller and selected entity remain shared. The existing Time Machine DOM
and controller are initialized only on first use. Live makes no analysis API
requests. History retrieval is an explicit existing Time Machine action.

Pre-flight reports repository, analysis, metrics, graph, hierarchy, retained
C scores, matching cached history and browser fullscreen capability. A GitHub
snapshot without cached history says “Not loaded”; a ZIP says unavailable.
A missing repository disables Launch and offers a direct ingestion link.
Missing optional evidence never blocks the whole presentation.

## Six compositions

| Scene | Composition and real evidence |
|---|---|
| Awakening | Existing Relic symbol, bounded light/title reveal, actual repository name; no repeated boot overlay or fictional initialization claims |
| Intelligence | Editorial identity beside four metric plates and included-file language bars; reuses LivingStatistics |
| Universe | Existing offline 3D/2D graph, real constellations, inspector, camera tools and guided tour; largest visible grouping chosen deterministically for Focus Structure |
| X-Ray | Existing directory/file/function exploration, breadcrumbs, direct traces and evidence; three columns on wide projectors, stacked on narrow displays |
| Risk & Time | Separate risk/history controls; up to six genuine scored C functions retained in graph, or original Time Machine and its honest unavailable/error states |
| Final reveal | Actual bounded graph endpoints projected decoratively in the background, true metric summary, explicit per-capability availability, restart and workspace return |

Files/functions/languages come from existing summary fields. Dependency count
includes only valid resolved internal CALLS/IMPORTS/INCLUDES edges, not ownership.
Missing numbers remain unavailable. Risk requires a C function, successful ML
status, valid predicted class and finite bounded saved score. No frontend
prediction, threshold change, calibration claim or Python ML output is added.
The graph may be capped: cards explicitly say **retained**, not all functions.

History must match the source URL and pinned 40-character anchor. Scene 5 reuses
existing history selection, filtering, tree/comparison availability and caching.
Newly retrieved history is reflected when the closing summary is rebuilt and readiness is refreshed on exit.

## State and interruption

`Sequence` models inactive → preparing → transitioning → active → exiting.
Each scene request increments a generation. An old animation callback cannot
activate a newer scene or undo an exit. There is one owned scene WAAPI animation;
changing scenes cancels it and finalizes numeric counting. Main transitions use
560ms, awakening 850ms and restrained cubic-bezier easing. Small logo/title
reveals are bounded CSS animations, with no perpetual background loops.
User actions never wait for a transition to complete. There is no autoplay.

Scene changes pause the existing graph, cancel its camera and tour, and cancel
Time Machine pending requests/playback. Async renderer initialization retains
its existing epoch guard. Graph rendering wakes only in the active Universe
scene. Hidden-document events suspend instruments. Pagehide destroys renderers,
closes storage and saves bounded view preferences; BFCache restoration reloads
and reobserves the existing controller. Repository pointer/expiry changes
invalidate the presentation instead of presenting stale evidence.

## Presenter operation and accessibility

Persistent Previous/Next, scene selector, progress, Fullscreen, Recording Layout,
Notes, Restart and Exit controls use existing rounded tokens. Controls remain
outside the scrollable scene. Headings receive programmatic reading focus;
interactive controls retain visible keyboard outlines. Exit restores launch
focus on pre-flight; Return to Workspace restores Overview and stored context.

Arrow keys, Space, Home, End and F are intercepted only outside native controls,
editable fields, dialogs and the investigation instruments. Escape respects the
existing X-Ray/tour behavior. Tour exit restores focus to the visible Live tour
button rather than the hidden duplicate workspace launcher.

Fullscreen is requested only by user interaction; rejection displays a useful
message without interrupting the scene. X-Ray only exits its own graph fullscreen,
not Live's outer fullscreen. Reduced motion is enforced in CSS and JavaScript:
no decorative reveals, immediate scene changes and final numeric values.

Recording Layout improves reading and removes redundant controls. It does not
capture video, redact repository contents or guarantee privacy. Review content
before sharing. Notes are hidden initially; enabling Recording Layout closes
notes. Opening notes explicitly warns that they appear on the audience display.

## Performance and responsive safeguards

No new runtime dependency. DOM work is bounded by existing graph/X-Ray policies;
risk cards cap at six, language rows at eight, decorative finale at 40 actual
nodes/100 actual edges. No physics or layout algorithm is replaced. Hidden
instrument cancellation reuses existing resource controls. Viewport sizing uses
flex and scrollable content, keeping navigation visible even with long evidence.
Projector and mobile checks cover 1920×1080, 1440×900, 1366×768, 1024×768 and
390×844. Four-times CPU throttling checks navigation recovery, not guaranteed FPS.

## Verification commands

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m pytest tests/test_product.py::test_real_documents_boot_with_shared_analysis_and_cross_page_navigation -q
# Use the product-fixture.json path produced by that test:
PRODUCT_FIXTURE=/tmp/pytest-of-jordan/pytest-XXX/test_real_documents_boot_with_0/product-fixture.json \
  node --test tests/frontend/*.test.cjs
.venv/bin/python tools/create_xray_acceptance_fixture.py /tmp/task11d-demo.zip
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8016 --no-access-log
chromium --headless --disable-extensions --remote-debugging-port=9229 \
  --user-data-dir=/tmp/codebase-task11d-chromium about:blank
PRODUCT_FIXTURE=/tmp/pytest-of-jordan/pytest-XXX/test_real_documents_boot_with_0/product-fixture.json \
  node tools/task11d_browser.mjs
```

Use an isolated browser profile; never the active personal profile. The browser
tool defaults to the dedicated ports above. Existing Task11B/11C suites accept
`BASE_URL`, `CHROME_DEBUG_URL`, `DEMO_ZIP`, and `ACCEPTANCE_OUTPUT` to preserve
historical evidence while rerunning regression acceptance.

## Evidence and limits

`reports/ui/task11d/browser.json` records actual Chromium checks, version and
source hashes. Six `scene-N.png` images are genuine 1920×1080 captures of the
five-file mixed-language ZIP. `local-git-history.png` uses actual seven-commit
Git history created by the existing pytest fixture and extracted through
`LocalReader`; its `owner/repo` identity is explicitly test metadata, not proof
of a live GitHub fetch. No screenshots or commit contents were generated by AI.
Fullscreen denial, missing graph and thrown-scene recovery are explicitly
labelled fault-injection cases. Normal analysis and graph data are not mocked.

Physical projector/low-end GPU, touch hardware, full screen-reader/WCAG and
external OBS recording acceptance are not certified. Headless fullscreen is
verified; desktop window-manager presentation can differ. Scroll is intentional
for long inspectors, histories and narrow screens. No private presenter channel
or built-in video recorder is claimed. Scientific model limitations are unchanged.

See [the live demo script](task11d_live_demo_script.md) for a six-minute walkthrough.

## Results and implementation review

| Check | Result |
|---|---|
| Baseline Python suite | 556 passed / 0 failed / 0 skipped, 17.40s |
| Final Python suite | 559 passed / 0 failed / 0 skipped, 21.81s |
| Frontend harness | 288 passed / 0 failed / 0 skipped (12 new Live cases) |
| Application JavaScript syntax | 33 files passed |
| RELIC // LIVE Chromium acceptance | 46 checks passed, no uncaught exceptions |
| Existing Universe Chromium regression | 83 checks passed, including strict local-script validation |
| Existing X-Ray Chromium regression | 52 checks passed, includes Task11A replay |
| Vendor integrity | Verified offline 3d-force-graph 1.73.3 bundle and notices unchanged |
| Frozen academic report validation | Valid against release `09f6b6d`; current development source intentionally differs |
| Report links | 61 local references/figures checked, none missing |

Python tests include wrappers that invoke frontend harnesses; these counts
should not be summed as independent Python tests. One pre-existing
Starlette/httpx deprecation warning remains. Browser execution used
Chromium 157.0.8103.79 in a dedicated headless profile, with no unsafe browser
sandbox flags. External HTTPS was blocked during offline Universe checks.

Manual screenshot inspection covered all six scenes and the genuine local-Git
history fixture. It prompted compact graph controls, side-by-side wide-screen
X-Ray plates and removal of an inappropriate interactive focus box from
programmatically focused headings; keyboard button focus remains visible.
A tour-exit focus defect specific to the relocated instrument was found and
fixed: the original tour launcher is hidden in Live, so focus now returns to
the visible Live launcher. Regression acceptance asserts this behavior.

Acceptance tooling corrections during bring-up: reset X-Ray to repository root
before testing a fixed drill-down path; test text-input shortcuts separately
from the scene selector's intentional native change behavior; wrap CDP async
storage operations in an async function; wait for CSS reveals before captures.
Assertions were not weakened and failed-run screenshots were not retained as
successful evidence.

Implementation commit: `8d1e5cc` (shared shell, instruments, native controls and
focused tests). Browser tools, receipts, screenshots and this documentation are
recorded in a subsequent evidence commit. No known critical application defect
remains from the completed checks; physical presentation and recording caveats
above remain appropriate rehearsal tasks.

A preinstalled Chromium extension injected `chrome-extension://…/page-script.js`
into the initial isolated profile. The existing strict local-script assertion
correctly rejected that run. Acceptance was rerun in a fresh temporary profile
with `--disable-extensions`; this does not disable Chromium sandbox protections.
The script-locality assertion remains unchanged, with an improved diagnostic
message identifying any unexpected URL. No personal browser profile was changed.
