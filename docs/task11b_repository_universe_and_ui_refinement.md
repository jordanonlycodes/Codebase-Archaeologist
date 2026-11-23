# Task 11B — Repository Universe and premium controls

## Release boundary and baseline

Work is confined to `feature/cinematic-experience`, starting from Task 11A commit
`ff760c7dac7a106dde9b9636e79fd6f2331d19a6`. Initial working tree was clean. Local `main`
and annotated `v1.0.0-university-release^{}` both resolved to the accepted Task 7E
commit `09f6b6df29b6b3e8e81c48c7f8f929a6e638dce5`. Neither reference is moved.
The model, academic documents, submission archives, brand assets and Task 11A boot/
statistics implementation are preserved. Existing features use their original routes.

Fresh baseline: `.venv/bin/python -m pytest -q` → **550 passed**, zero failed/skipped,
19.65 seconds, one existing Starlette/httpx deprecation warning. Existing frontend
harnesses contained 230 cases. No animation/3D framework or external service was added.

## Repository Universe

The renderer remains the verified local `3d-force-graph@1.73.3` bundle. All graph data
comes from the existing snapshot. There is no second 3D engine, source analysis pass,
synthetic dependency, fabricated module or inferred defect probability.

### Constellation mapping

`graph/universe.js` is a pure presentation module. Its rules are:

1. Use genuine retained `CONTAINS`/`DEFINES` hierarchy to find a node's directory owner.
2. A directory entity anchors its own directory grouping. Files orbit their directory;
   functions orbit their evidenced owning file.
3. Where ownership is unavailable, group by the parent of the actual relative path.
   Root files are labelled **Repository root**. Missing locations are explicitly labelled
   **Location unavailable**, never assigned an invented path or runtime module.
4. Sort groups by path/ID and members by stable entity ID. Fixed orbital formulas,
   directory cells, bounded depth and occupancy separation yield repeatable coordinates.
5. The repository entity remains a real repository anchor. Directory captions and node
   rings are DOM presentation annotations; they add no graph entities or relationships.

Automatic **Knowledge graph + 3D Universe** uses this layout. Explicit Hierarchical/
Radial choices and analytical call/dependency perspectives retain existing arrangements.
Selection, overlays and harmless refreshes do not restart physics, rerun layout or
resubmit graph data. User-dragged positions survive styling updates. Reload restores a
deterministic layout, rather than inventing a new random universe.

The directory dropdown lists actual visible membership, with a distinction between
retained ownership and relative-path grouping. These are directory constellations, not
claims about runtime modules or an alternative architecture reconstruction algorithm.

### Camera behavior

- Selecting a real node smoothly frames it and its visible direct neighbors, with a
  minimum contextual distance to avoid oversized close-ups. The inspector updates at
  once, before the transition completes.
- Selecting a retained directory frames its visible directory grouping. **Frame
  constellation** frames the selected dropdown grouping without adding an entity.
- **Fit** frames the current filtered view. **Reset Universe** clears selection/view
  filters and restores the full bounded knowledge view and default camera direction.
- Perspective-aware framing computes horizontal/vertical/depth extents and marker
  padding. It handles zero-distance camera vectors, narrow aspect ratios and single
  nodes, and rejects invalid coordinates/empty bounds.
- Camera requests share one owned RAF transition and generation guard. Later requests,
  pointer input, wheel input, keyboard panning, pause and destruction cancel earlier
  movement. Durations are bounded to 1,200 ms; ordinary focus is 650 ms, directory
  framing 780 ms and Fit 620 ms. Reduced motion makes these immediate.
- Hidden viewport requests set their valid framing immediately without an animation;
  an automatically fitted viewport refits when it becomes visible. Manual camera
  positions remain preserved. Labels synchronize at the end of a camera transition.
- Manual orbit, pan, zoom, node arrangement and viewport arrow-key panning remain
  available. There is no idle auto-rotation or camera movement that competes with input.

### Dependency illumination

All illumination uses actual edges in the filtered visible view. Incoming/outgoing
relations keep their recorded direction; no unresolved reference becomes an internal
edge. The selected marker is brighter/larger. Direct neighbors remain bright and
unrelated nodes remain visible at lower emphasis. Edge arrows preserve real direction
and relationship-type encoding.

For non-color-only encoding, the selected marker has a larger solid ring, incoming
neighbors have dashed rings, outgoing neighbors have small plain rings and mutual
neighbors have double rings. The legend describes these distinctions. Existing
complexity and C-only ML overlays keep their own meanings. Connectivity is not risk.

### Investigation inspector

The panel now leads with **ENTITY INSPECTION**, type, name, source path and explicit
incoming/outgoing retained-edge counts. Counts cover the retained snapshot; illumination
follows the current filters, as stated in the panel. Existing source lines, structural
metrics, evidence locations, unresolved references and stable-ID navigation remain.
Navigation actions are grouped under **Continue the investigation**.

Actual eligible C functions may show their existing uncalibrated research estimate.
Python functions explicitly remain unscored. Graph degree, grouping and camera focus
never produce a probability or confirmed-defect claim. Long names wrap; stable IDs
retain horizontal inspection when needed. The inspector moves below the graph on narrow
layouts, where it has its own bounded vertical scroll area.

### Guided tour

Click **Explore Universe** on the Knowledge explorer page. The controls expose **Pause
tour / Resume tour**, **Skip scene** and **Exit tour**. Escape exits. Pointer, wheel or
keyboard navigation ends the tour immediately. Focus moves to the tour controls at
start and returns to the start button on exit/completion where appropriate.

For a local demonstration, restart the application after pulling this branch (or run
Uvicorn with `--reload`) so its new graph asset registration is loaded, then refresh
Chromium. Import a repository, open **Knowledge explorer → 3D Universe**, and choose
**Explore Universe**. Existing personal browser sessions need not be closed.

Scenes are chosen from the current visible graph:

| Scene | Evidence-based rule |
|---|---|
| Overview | Actual visible node/edge totals, explicitly a bounded view |
| Major directory | Largest visible directory membership; ties broken by label/ID |
| Relationships | Highest visible CALLS/IMPORTS/INCLUDES incident count, then total incident edges, then stable ID |
| Investigation | Real function preferred, then file, ranked by incident edges and stable ID |
| Return | Fit the original current view; selection clears |

Membership/degree are navigation rules, not quality or risk rankings. Scenes without
supporting structure are omitted. Empty graphs cannot start a tour. A single repository
anchor has a one-scene tour. Playback advances every 3.8 seconds; there is at most one
timer. Pause/resume/skip/exit replace or clear that timer, guarded against stale callbacks.
Changing graph filters or repository cancels playback. Page hiding pauses, navigation
ends it, and tour-only listeners are removed on exit. Reduced motion presents the same
real scenes with immediate framing and manual **Skip scene** advancement.

### Performance and fallback

The original caps remain **180 nodes / 420 edges**, with accessible search across the
retained graph and explicit truncation/coverage messaging. No extraction limits change.
The existing quality policy, pixel-ratio bounds, low-power renderer, no requested MSAA,
label collision handling and idle/hidden rendering suspension remain in place.

Captions are capped to 12 directory labels (6 in Performance). Node label/halo budgets
follow existing quality limits. Halos are small DOM borders associated with real nodes;
there are no added lights, bloom passes, shaders or particle systems. Fixed node
coordinates avoid ongoing physics. Work is bounded by the visible graph.

WebGL initialization errors retain the existing SVG fallback and accessible entity
browser. A real `webglcontextlost` event now cancels movement/tours and switches to the
same retained evidence in 2D, preserving selection and filters. A new 3D context can be
requested afterward. Tours also provide accessible 2D evidence scenes if WebGL is not
available. No CDN is used as a fallback.

Screenshot inspection exposed a real integration defect: the bundle injects tooltip/
navigation CSS inline, which the existing `style-src 'self'` policy blocks. A populated
tooltip could occupy normal flow and offset the canvas from projected labels. Explicit
`.graph-canvas`-scoped rules now position those known library surfaces correctly, style
the tooltip and keep the redundant vendor gesture legend hidden. A real hover test
asserts an absolute tooltip and unchanged canvas origin. The bundle bytes and CSP remain
unchanged. Browser policy notices about the blocked vendor style injection may still
appear; the external integration styles handle it without allowing arbitrary inline CSS.

The same browser investigation found that version 1.73.3 coerces DOM-element label
callbacks to `[object HTMLSpanElement]`. Node/link label callbacks now supply strictly
escaped strings to the library's HTML tooltip API. Exact escaping is tested with
malicious-looking node and edge labels; the real hover test verifies the visible source
name/path. Camera moves also update OrbitControls and camera matrices before projecting
labels, using their existing public APIs.

## Shared premium control system

`product/controls.css` is loaded after feature styles in both Jinja base templates.
Central HTML selectors deliberately outrank legacy component radii, without `!important`
and without targeting SVG graph nodes or third-party renderer internals. The explicit
tooltip integration in the graph stylesheet is scoped separately to that viewport.

| Token | Value | Use |
|---|---:|---|
| `--radius-xs` | 6 px | Small status tags and graph labels |
| `--radius-sm` | 9 px | Inputs, selects, compact controls and navigation |
| `--radius-md` | 12 px | Ordinary secondary actions and bounded panels |
| `--radius-lg` | 16 px | Primary actions, disclosure/import surfaces |
| `--radius-xl` | 20 px | Available larger-surface token; not indiscriminately applied |
| `--radius-pill` | 999 px | Circular zoom controls |

Primary Analyze, Jordan Investigate and Explore Universe actions use the 16 px family.
Header/export/forget, pagination, camera and other compact actions use 9 px. Ordinary
buttons default to 12 px. Tabs/mode controls use restrained 9 px corners rather than
turning every action into a pill. Dynamically generated inspector, search, timeline,
churn, Jordan and comparison controls inherit the same system.

Hover uses a border/shadow emphasis and at most a one-pixel lift. Press uses a small
translation/scale without layout changes. Keyboard focus has a contrasting two-pixel
outline. Disabled controls retain clear muted styling and suppress lift/shadow. Labels
and genuine loading indicators stay intact. Motion preferences disable movement.

At mobile/coarse-pointer sizes, buttons and text/select form controls have a 44 px
minimum height; zoom icons also have a 44 px minimum width. Layouts wrap instead of
forcing horizontal overflow. Textareas keep their existing rows and native behavior.

### Global audit scope and deliberate exceptions

Audited landing, import and all nine workspace pages: Overview, Risk, Structure, Graph,
Architecture, Heatmaps, Blast Radius, Jordan and Time Machine. The audit covers primary,
secondary, disabled, icon, header/footer, tab, upload, submit, replay, skip, export and
dynamic actions; text inputs, textareas, selects and the existing disclosure surface.

Tables, chart/canvas regions, architecture SVG rectangles and other evidence geometry
retain their analytical shape. Native browser confirm dialogs, checkbox/radio/range/file
widgets and native SVG-title tooltips remain platform-managed. They are not legacy HTML
buttons overlooked by the radius system. No new modal/account/cloud flow is introduced.

## Validation and browser evidence

Focused implementation validation passed 39 graph/universe cases initially and all
targeted Python/product tests. Added universe cases cover grouping, deterministic layout,
bounded/disconnected/missing data, direction/filter illumination, framing, camera safety,
tour transitions, reduced motion and cleanup. Existing product handoff assertions now
find the same action buttons inside their new grouped container; their navigation and
entity-identity assertions are retained. Four new product cases exercise actual
controller grouping, 2D tour controls, cancellation on filters/repository changes and
manual reduced-motion scenes.

The native CDP helper now waits for the new main-frame commit and destination URL,
rather than trusting the previous document's `readyState=complete`. Navigation failures
are reported explicitly. Screenshot capture additionally waits for actual 3D meshes,
camera settlement and rendered frames; a screenshot of pre-rendered captions is not
treated as proof of a loaded scene.

Browser: sandboxed headless Chromium 157.0.8103.79, isolated temporary profile on the
Linux desktop host, local test server on port 8014. Normal browser profiles and the
user's port 8000 application are not used for the test. External HTTPS is blocked while
testing graph and workspace navigation. The original three-directory fixture from
`tools/create_acceptance_fixture.py` produces **3 files, 12 graph entities, 14 retained
relationships, 3 directory groupings and 3 genuine C predictions**. The fixture is source
analyzed by the real API, not a hardcoded graph response.

Exact measured checks and current source hashes are recorded in
`reports/ui/task11b/browser.json`. Browser acceptance covers actual pointer selection,
orbit/pan/wheel, focus/Fit/reset, rapid camera requests, directory framing, matching
dependency evidence, tour start/pause/resume/skip/exit, automatic advance/Return, keyboard
override, reduced motion, true context-loss fallback, C/Python distinction, dynamic
actions, focus/hover/disabled states and all page/control audits at **1440, 1024, 768
and 390 px**. The empty-graph case is explicitly a presentation test fixture, not a
claim that the imported repository had no entities. Mobile visible-button heights are
checked in addition to overflow and computed corner radii.

Actual Chromium captures (no image-generation or image-editing step):

- `reports/ui/task11b/universe.png` — complete bounded directory constellation view.
- `reports/ui/task11b/inspection.png` — real C-function selection and evidence inspector.
- `reports/ui/task11b/tour.png` — guided relationship scene.
- `reports/ui/task11b/overview.png`, `import.png`, `jordan.png`, `time-machine.png` — shared controls.
- `reports/ui/task11b/mobile.png` — rendered graph and stacked inspector at 390 px.

Reproduce in separate terminals from the repository:

```bash
.venv/bin/python tools/create_acceptance_fixture.py /tmp/task11b-demo.zip
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8014 --no-access-log
chromium --headless --disable-extensions --remote-debugging-port=9227 \
  --user-data-dir=/tmp/codebase-task11b-chromium --window-size=1440,1100 about:blank
node tools/task11b_browser.mjs
```

Use a dedicated temporary profile; do not target a personal browser session.

Regression commands:

```bash
.venv/bin/python -m pytest -q
node --test tests/frontend/universe.test.cjs tests/frontend/graph.test.cjs
.venv/bin/python tools/verify_vendor_assets.py
.venv/bin/python tools/check_report_links.py
.venv/bin/python tools/validate_report.py --source-ref 09f6b6df29b6b3e8e81c48c7f8f929a6e638dce5
```

## Files and remaining scope

New presentation files: `app/static/graph/universe.js`, `app/static/product/controls.css`.
Integration: `graph/three.js`, `graph/explorer.js`, `graph/explorer.css`, graph template,
two base templates and graph asset registration in `app/routes/dashboard.py`.
Verification: `tests/frontend/universe.test.cjs`, `tests/test_universe.py`, existing
product harness, `tools/task11b_browser.mjs` and the native CDP helper.

No hardware GPU/FPS benchmark, screen-reader reading-order certification, full WCAG
audit or physical-touch-device certification is claimed. The accepted 2D fallback and
bounded search remain useful when 3D is unavailable. Viewport labels may be omitted to
avoid overlap and to respect budgets; inspector/search still expose retained identities.
Directory grouping is structural, not evidence of runtime boundaries. Task 11C remains
a separate task; no report, model or release archive regeneration is part of this work.

## Closing verification checkpoint

- Full final `.venv/bin/python -m pytest -q`: **553 passed**, zero failed/skipped in
  **17.07 seconds**, one existing Starlette/httpx warning. Three Python regression
  entries were added. No tests were removed or skipped.
- **247 frontend cases**: 155 across eight standalone harnesses, 84 in the real-document
  product harness and 8 Time Machine cases, all exercised by the Python suite. This is
  230 existing cases plus 13 Universe and 4 product-controller cases. Existing tooltip
  expectations were corrected to the actual library string API and strengthened with
  malicious-looking label escaping assertions.
- **31 application JS files / five QA modules** passed Node syntax checks.
- **83 genuine Chromium checks** passed, including 44 page/viewport control audits,
  actual hover/pointer interactions, camera/tour lifecycle, 44 px mobile button targets,
  context loss and offline rendering. No uncaught JS exceptions. Source hashes in the
  browser receipt match the tested application files. Representative captures were
  visually inspected, including the loaded mobile graph, inspector, tour and import UI.
- **61 local links/figures** passed. Reviewed offline vendor integrity passed. The
  frozen Task 7E report remains validated against its exact release SHA by the existing
  read-only report regression. Release/model/brand/Task 11A presentation files have no
  changes relative to entry commit `ff760c7`.

Implementation and QA are committed separately on the cinematic development branch.
The source checkpoint and final publication verification are recorded below; no merge
into `main`, tag movement or archive rebuild is part of this task.

Implementation checkpoint: `722a58a` — `Build repository constellations, guided universe
tour and premium shared controls`. The following QA commit contains the native browser
runner, navigation-settlement correction and actual acceptance captures/receipt. Final
local/remote feature-branch equality is checked after publication; Git refs provide the
closing commit identity without a circular self-hash in this document.
