# Architecture Intelligence and Repository Heatmaps — Task 4C.1

The `architecture` response component (schema `1.0`) is assembled after the existing
shared inventory → structural → ML → knowledge-graph pipeline. Both ZIP and GitHub
imports use it. No source is reparsed, imported, executed or downloaded by this engine;
no model is retrained. The UI switches cached views without another request.

## Evidence and component grouping

A component is an **immediate parent directory's direct member files**. Files in
`src/main.py` and `src/lib/helper.py` belong to `src` and `src/lib`, respectively.
Root-level files use the explicitly named `(root files)` component, path `.`. Empty
unretained directories are not invented. Components partition retained files, so their
counts do not double-count descendants. They are directory-based groups, not inferred
services, controllers, databases, layers or runtime modules.

The heatmap has a separate nested directory hierarchy. Its `src` region aggregates
both files above, including descendants. This distinction is intentional: component
membership is non-overlapping, whereas directory drill-down describes nested totals.

IDs are domain-separated deterministic graph hashes for components and aggregate
edges. File and function identities reuse Task 4A.2 IDs. Directory heatmap IDs reuse
existing graph directory identity conventions; the heatmap root has its own stable ID.
`graph_id` links only to actually retained graph nodes, where available. Identities
are snapshot-local, not guarantees across file moves or arbitrary edits.

## Architecture engine and response

`app/analysis/architecture/` separates typed dataclass contracts (`models.py`) from
evidence aggregation (`engine.py`). `reconstruct(result)` reads existing results only.
The optional `AnalysisResult.architecture` field contains:

- `components`: membership IDs, metrics, graph link, incoming/outgoing component IDs,
  same-component counts and bounded unresolved-reference IDs/counts.
- `edges`: directed type-specific component aggregates with retained graph-edge counts,
  source occurrence counts and bounded original edge-ID samples.
- `heatmap`: flat parent-linked file/directory nodes, metrics, source/ML status and links.
- `dependency_cycles`, evidence-based `findings`, `summary`, `coverage`, `limits`,
  `definitions` and `schema_version`.

Existing API fields remain; the existing JSON export includes this component automatically.
No persistent repository storage or separate architecture endpoint is introduced.

### Relationships and cycles

Only retained resolved **CALLS**, **IMPORTS** and **INCLUDES** edges contribute semantic
relationships. Direction is caller → callee, importer → imported file, or including
file → included file. Aggregate keys are `(source component, target component, type)`.
A component pair may therefore have several relationship types. Original graph edges,
source occurrences and component aggregates have distinct counts. Same-component edges
are counted separately, preserving recursive calls without artificial inter-component
self-dependencies. CONTAINS/DEFINES inform hierarchy, not semantic dependency counts.

An aggregate retains original graph-edge IDs; source reference and path/line/column
evidence remain in the knowledge graph. The inspector exposes these bounded samples.
Unresolved, ambiguous and unsupported dynamic references remain explicit records and
never become confirmed dependencies. Missing graph nodes, component caps and omitted
edges have coverage counters; absence of an edge does not prove independence.

Iterative Kosaraju strongly connected components detect groups of at least two
components connected cyclically through **IMPORTS/INCLUDES only**. Calls alone do not
establish a dependency cycle. Aggregation can overapproximate file-level cycles because
different files within a directory may participate in different edges. These are
observed static component cycles, not guaranteed runtime or build cycles. Single-
component internal dependency cycles are not reconstructed by this feature.

Findings select actual retained leaders by inventoried bytes, observed function count,
maximum function complexity, hotspot count and distinct connected components. They
include measured values and navigation to evidence; none is an architecture verdict,
validated quality score or inferred probability.

## Metrics, availability and heatmap semantics

| Metric | File definition | Directory/component aggregation |
| --- | --- | --- |
| Physical lines | Existing inventory lines, including comments and blanks | Sum of retained members/descendants |
| Bytes | Existing inventory byte count | Sum |
| Observed functions | Valid analyzed structural functions | Sum of available counts |
| Maximum function complexity | Maximum valid function cyclomatic complexity | Maximum, never an average |
| Total complexity (API) | Sum of valid function complexity | Sum of available totals |
| Structural hotspot functions | Existing hotspot function IDs | Sum of available counts |
| Max observed C-function score | Maximum actual estimated score among reliably linked analyzed C functions | Maximum of actual scores, never their average |

The ML measure is a **maximum function-level review signal**, not a file/directory
prediction or defect probability. Source-location/name/index matching is checked;
Python and other unsupported ML languages never receive scores. Model absence does not
prevent structural metrics, hierarchy or architecture analysis.

`measured_files` gives per-metric covered-file counts, alongside total files and scored
function counts. Unsupported/unavailable function measurements remain null. Completely
analyzed no-function files have function/hotspot counts zero, but no maximum complexity.
A valid score of zero is measured, not unscored. Partial parses can contribute observed
valid functions; they are not silently presented as complete. A maximum may be unavailable
in an otherwise fully parsed empty file, so metric coverage is not a parser-success rate.

Heatmap **area** independently selects physical lines or bytes. Weighted balanced binary
partitioning divides sibling rectangles; weights have a minimum of one per sibling
entry so empty files remain selectable. This visibility floor can distort tiny/zero
regions and is disclosed in the legend. Non-ML **color** uses square-root intensity from
zero to the largest visible leaf-region value. Collapsed directory regions can supply
that maximum. The scale can change when drilling down; compare numeric values in the
inspector rather than assuming cross-view color equivalence. ML colors use a fixed 0–1
linear scale of the existing uncalibrated function scores.

Expanded directory containers have neutral surfaces; files and unexpanded directory
regions show metric intensity. Hatching means unavailable/unscored; tooltip and inspector
explicitly distinguish unsupported, unscored and missing data. Partial coverage uses a
dashed outline. Measured zero uses a neutral solid fill. Labels appear only when region
space permits, while title/keyboard inspection retains names and values.

## Frontend architecture and interactions

`app/static/architecture/` is self-contained for a future dedicated page:

- `data.js`: cached indexes, bounded component subsets, metric states, treemap geometry,
  breadcrumbs and membership lookup.
- `scene.js`: event-driven SVG viewport, directional markers, pointer/keyboard controls
  and animation-frame-coalesced pan/zoom.
- `explorer.js`: shared architecture/heatmap context, safe text rendering, source inspector,
  findings, evidence and navigation into the existing Knowledge Graph Explorer.
- `explorer.css`: scoped Black & Crimson presentation, editorial serif emphasis and
  existing interface sans-serif typography. No remote fonts or effects pipeline.

The component canvas reuses the existing cycle-safe directed layout utility, folded
into spatial bands for bounded overview. These positions are a display arrangement,
not an execution order or inferred architecture layer. Component containers show actual
file/function counts. CALLS, IMPORTS and INCLUDES use distinct link colors/styles;
selection emphasizes incoming/outgoing links and dims unrelated components. Selecting
an edge opens aggregate/source evidence. Selection preserves the existing layout.

Controls provide zoom/pan, fit/reset, relationship filtering, component selection,
focused connections, search and clear repository focus. `Explore directory heatmap`
opens the same path, directory regions drill down, breadcrumbs/Parent navigate upward,
and clicking files opens inspection in their parent directory. Metric changes reuse
cached geometry; changing the area metric recalculates it. The inspector paginates
files and links retained files/functions to the existing graph. Missing graph links
are absent or disabled. Findings and cycle entries navigate to actual components.

Two nested directory levels are rendered at once. A frame may omit regions because of
its cap; the status explicitly reports this, and area is then normalized among shown
siblings. Search covers all retained heatmap paths, including those outside the frame.
Component views rank by retained incoming/outgoing connectivity, then bytes and path;
the selected matching component remains visible within the bound. Switching views does
not reanalyze. A new repository disposes the old scene and clears selection/caches.

## Bounds, safety and performance

| Layer | Bound |
| --- | ---: |
| Backend heatmap nodes (including root) | 10,000 |
| Backend components / component-edge aggregates | 1,000 / 8,000 |
| Original graph-edge IDs per aggregate | 8 |
| Unresolved reference IDs per component | 16 (full retained count preserved) |
| Canvas components / relationships | 24 / 100 |
| Treemap regions / nested levels | 160 / 2 |
| Search hits / paginated file rows | 30 / 25 |
| Inspector relationship samples per direction | 16 |

Backend bounds live in `ArchitectureLimits`; original ingestion/structural/graph bounds
continue to apply. Algorithms are iterative/bounded and use indexed owners/memberships,
not all-pairs source matching. Component/heatmap output has count bounds; there is no
new claim of a separately enforced serialized-byte budget. Coverage separates own
truncation, upstream graph/structure truncation, unmapped semantic edges/references,
retained files and metric coverage. All values describe retained evidence.

There are no WebGL contexts, force simulations, continuous render loops or new dependencies
for this feature. Topology/area changes build geometry; selection and metric color changes
reuse it. Pan/zoom are scheduled, and source content is not retained in the new response.
Text is inserted as text, never HTML. SVG events/observers/queued frames are removed on
repository replacement. Reduced motion disables the short CSS state transitions.
No actual FPS, memory or smoothness measurements are claimed.

## Verification and limitations

Implementation verification: **381 Python tests passed, 0 failed, 0 skipped**. This
includes **25 architecture backend cases**, two architecture frontend/API checks and
the existing suites. The browser-free frontend runners cover **9 architecture cases**
and the existing **24 graph cases**; those Node cases are not additional Python tests.
One existing Starlette TestClient deprecation warning remains.

Checks cover grouping, nested sums/maxima, nullable metrics, cyclic/recursive dependencies,
reference/evidence caps, deterministic IDs/results, upstream truncation, real score
linkage, missing models, API/JSON contracts, mocked GitHub/ZIP equivalence, treemap
bounds/weights, cached geometry, view context, safe labels and scene cleanup.

A real mixed C/Python ZIP smoke test retained 8 files, 5 components and 13 heatmap nodes.
It produced 3 cross-component aggregates (3 source edges/occurrences) and 1 internal
component edge. Four functions were measured, maximum complexity was 1 and total
complexity was 4. The trusted local model was ready and analyzed the two C functions.
Header structural metrics remained unsupported, correctly making structural coverage
partial, while graph extraction completed. No cycle or unresolved reference was observed
in that fixture; this is not a general completeness claim.

Chromium startup was attempted and failed with `setsockopt: Operation not permitted`.
Visual layout, responsive appearance, live browser interactions and live GitHub imports
were not verified here. Design review inspected layout rules, bounds, spacing, readable
states, safe text, working event paths and data semantics; it is not a substitute for
browser inspection. Dense diagrams can still cross edges or require zoom. Direct-parent
groups are not a recovered semantic architecture. Frontend resource bounds intentionally
show subsets. Heatmap maxima cannot establish defects or calibrated probabilities.

Local verification:

```bash
source .venv/bin/activate
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
# In another terminal:
node tests/frontend/architecture.test.cjs
pytest tests/test_architecture.py tests/test_architecture_frontend.py -q
pytest -q
```

At `http://127.0.0.1:8000`, analyze a small known repository with nested C/Python files,
imports/includes and recursion. Check component membership and link direction against
source; inspect exact call sites; open heatmap, try all six color metrics and both area
metrics, follow breadcrumbs and select an unscored Python file. Follow a graph link,
switch views, clear focus and replace the repository. Repeat with unsupported-language
and partial/limited inputs. Inspect at 1366×768 and narrower widths, with keyboard and
reduced motion; ensure long paths and evidence remain accessible. Export JSON and compare
counts independently of visualization bounds. Record measurements before making any
performance claim.

The academic PDF/DOCX report remains unchanged for the planned Task 7 update.


## Blast Radius handoff (Task 4C.2)

Component, file and directory inspection can launch the [Blast Radius Explorer](blast_radius.md)
using stable component/graph IDs. Component origins expand immediate member files;
directory origins expand retained descendants. Impact inspection can return to the
corresponding component canvas or file heatmap without reanalysis. Reached function
owners map to existing files/components; containment is not an impact propagation edge.
No architecture grouping, metric definitions, trained model or heatmap aggregation changed.
