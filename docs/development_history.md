# Knowledge Graph Explorer development history

This history records implementation evidence and regression results. It is not a
browser benchmark or an academic evaluation. See [current explorer documentation](knowledge_graph.md#interactive-explorer-task-4b2)
for behavior, limits and local verification instructions.

## Backend foundation — Task 4B.1

Commit: `61dd966035c8c01befe6c1bad2aee2265a9a073e`

The shared ZIP/GitHub pipeline gained one bounded, deterministic graph representation:
repository/directory/file/function hierarchy, supported C/Python calls, imports/includes,
conservative resolution and explicit unresolved references. Structural identities,
metrics and actual C-only ML information were reused. No graph database was introduced.

Recorded verification: **348 Python tests passed, 0 failed, 0 skipped**. A mixed-language
ZIP smoke test retained 13 nodes, 16 edges and two unresolved references. Those counts
belong to that fixture, not an arbitrary repository.

## Initial hybrid explorer — Task 4B.2

Commit: `763f3d42a8274ada4bc254c91b74819b7381e570`

The frontend added a shared graph index/controller, dependency-free SVG adapter and
optional local `3d-force-graph 1.73.3`/Three.js adapter. Perspectives, filters, search,
inspection, overlays, neighborhoods and renderer state sharing used actual retained
results without another analysis request.

Recorded verification: **354 Python tests passed, 0 failed, 0 skipped**, including the
frontend runner; **13 Node cases passed**. Initial asset retrieval failed because DNS
was restricted. Missing 3D assets produced an explicit 2D fallback. Uvicorn initialized
but could not bind the local port; Chromium startup was blocked by socket permissions.
No real 3D rendering, responsive-layout success or FPS measurement was established.

## Layout, rendering and usability refinement

Commit: `ff0ea45305c6bd1ecb24372f6afb969c412f8140`

The following problems were identified from the existing code paths and requested
usability corrections. The solutions have unit/adapter evidence; visual quality remains
subject to unrestricted local browser checks.

| Original problem | Implemented solution | Regression evidence |
| --- | --- | --- |
| All perspectives used a generic distribution | Shared packed hierarchy, directed SCC layers and directory clusters; explicit hierarchical/radial choices | Deterministic strategy and positioning tests |
| Crowded entities and unrelated groups | Spaced subtree packing, neighboring-cell collision checks, bounded overview and group/branch controls | Hierarchy, collision, collapse and hidden-search tests |
| SVG scene replaced during every interaction | Keyed retained nodes/edges, separate geometry/style/viewport updates and animation-frame batching | Element identity, preserved positions and queued-update assertions |
| Selection/overlay changes resubmitted 3D graph data | Topology/layout signature, reused node objects and fixed coordinates | Unchanged graph-data/layout counters in all three perspectives |
| Unnecessary simulation and idle graphics work | Zero force warmup/cooldown, interaction wake windows, offscreen/idle pauses and conservative graphics settings | Mocked simulation, pause and cleanup contracts |
| Labels dominated or overlapped the view | Contextual priority, collision suppression, bounded projection pool and zoom-dependent 2D labels | Selected/hovered priority and collision tests |
| Relationships were hard to distinguish | Type-specific colors, 2D dash styles, directional emphasis, curves and retained occurrence/evidence inspection | Dependency direction, recursion/cycle and occurrence assertions |
| Perspective changes silently retained incompatible controls | Explicit type/relationship/language reset notice and incompatible focus/selection removal | Shared-controller state tests |
| Inspector displayed irrelevant empty function fields | Entity-specific identity/source/structural/ML groups; full paths/IDs and expandable evidence | Directory inspection and safe text-rendering assertions |
| Renderer replacement could leave stale work | Cancellation of async attachment, frames/timers/listeners/observers and WebGL resource disposal | Renderer/repository switching and idempotent cleanup tests |

The automated matrix exercises **2D and 3D × Knowledge, Calls and Dependencies**.
Recorded final results: **354 Python tests passed, 0 failed, 0 skipped**; the suite
includes a runner for **21 passing Node frontend cases**. JavaScript syntax, dependency
consistency and diff checks passed. One existing Starlette TestClient deprecation
warning remained. Restricted Python execution used process-local selector polling;
application code was not changed to accommodate that sandbox limitation.

At this stage local 3D vendor assets were present. The bundle matched its existing
receipt and was preserved unchanged as untracked user files. This did not remove the
browser blocker: Chromium exited with `setsockopt: Operation not permitted`. The
adapter tests use DOM/WebGL-library mocks and do not measure real camera/drag behavior,
GPU rendering, responsive appearance, FPS, memory savings or latency. No quantitative
performance improvement is claimed.

## Documentation reconciliation

The documentation-only follow-up consolidates current README features/setup, algorithms,
graphics preferences, lifecycle/coverage limits, browser limitations and a reproducible
local performance-check procedure. It also corrects superseded label budgets and avoids
presenting historical download failures as the current state of every installation.

Evidence sources: committed implementations in `app/static/graph/`, dashboard controls
in `app/templates/dashboard.html`, regression cases in `tests/frontend/graph.test.cjs`
and `tests/test_graph_explorer.py`, recorded implementation test outputs and the Git
commits above. Documentation checks are reported separately from historical full-suite
results; changing prose does not imply a fresh application benchmark.

The academic PDF and editable Word report remain unchanged. These improvements will
be candidates for the comprehensive academic report update during **Task 7**; that
update has not been performed here.

Documentation-follow-up checks: 21 frontend cases passed again; all 17 local Markdown
links/anchors across the three updated documents resolved, code fences were balanced,
and `git diff --check` passed. The recorded 354-test application regression result is
from the implementation verification, not a new full-suite run for this prose-only change.


## Hardware-informed quality controls — continuation of the performance patch

User feedback reports Intel HD Graphics 620, Arch Linux/Hyprland/Wayland, Mesa 26.2.7,
Chrome 155 ANGLE/OpenGL, 1366 × 768, hardware acceleration and zero GPU-process crashes.
The reported `msaa_is_slow` / `msaa_is_slow_2` workarounds prompted inspection; they
are not a diagnosis of this application's stuttering.

Inspection confirmed the existing renderer already used `antialias: false`; its WebGL
capability probe did not explicitly set that attribute. The probe now also requests no
antialiasing. Added shared Auto/Performance/Balanced quality controls preserve the
previous 2D/3D layouts, perspectives and overlays. Performance caps pixel ratio at 1,
uses resolution-4 spheres, reduces label work and requests arrowheads only for relevant
relationships. Balanced caps ratio at 1.5 with resolution 6. Auto starts conservatively
and can step down after two sustained slow active-interval windows. No GPU-specific
rules, browser flags or security changes are used. Frame sampling is a heuristic;
actual GPU cause and quantitative benefit remain unmeasured.

Recorded follow-up checks: **354 Python tests passed, 0 failed, 0 skipped**, including
the frontend runner; **24 Node cases passed**. Regression coverage includes disabled
antialias requests, profile/state preservation, topology/position reuse, arrowhead policy,
idle-gap exclusion and non-oscillating adaptation. One existing Starlette deprecation
warning remains. The academic reports and local untracked vendor assets are unchanged.
See [hardware/quality details](knowledge_graph.md#hardware-feedback-and-adaptive-quality)
for the exact settings and local comparative verification procedure.
