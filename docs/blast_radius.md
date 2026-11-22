# Blast Radius Explorer — Task 4C.2

## Current product workflow — Task 5

The explorer now lives at `/workspace/blast-radius`, a dedicated document with only
its own feature initialization. Import at `/explore` once, then navigate freely with
the same expiring source-free snapshot. Graph, architecture and heatmap inspection can
launch this page with stable IDs; impact inspection can return to those pages without
reanalysis. Origin/depth/direction preferences survive ordinary navigation and refresh.
The API remains unchanged; exporting from this workspace includes its selected bounded
query. Other workspace exports contain the full original analysis snapshot.

The anchored layout and all traversal/evidence semantics below are preserved. Neutral
surfaces, editorial shell typography and readable evidence controls replace the old
combined dashboard. See [frontend lifecycle and retention](frontend.md). Verification
numbers below are historical; the README records the final Task 5 suite.

## Scope and architecture

The explorer answers **which retained entities are statically reachable, and through
which observed relationships?** It does not predict breakages, runtime execution,
defects, exploitability or calibrated probabilities.

`app/static/impact/engine.js` is the single reusable impact query engine, used unchanged
in the browser and Node tests. It consumes the existing `knowledge_graph`, `architecture`
and `structural` response components. `explorer.js` handles state, inspection and
cross-feature navigation; `explorer.css` scopes its presentation. No parser, graph
extraction implementation, server-side repository store, model or dependency is added.
This is client-side analysis over the retained snapshot, not a new server impact API.
The modules can move to a dedicated workspace page without changing ingestion.

The engine builds incoming/outgoing semantic adjacency, membership, file-owner,
component and reference indexes once per completed repository analysis. IDs are the
existing snapshot-local graph/structural/component IDs, never name-only matches.
Unresolved and ambiguous records are references, never confirmed internal edges.
Only resolved edges with both endpoints retained enter traversal.

## Direction and membership

| Source evidence | Direction | Upstream | Downstream |
| --- | --- | --- | --- |
| CALLS | Caller → callee | Reverse edges to potential callers | Forward edges to callees |
| IMPORTS | Importing file → imported file | Reverse edges to importing files | Forward edges to imported files |
| INCLUDES | Including file → included file | Reverse edges to including files | Forward edges to included files |
| DEFINES / CONTAINS | Membership only | Never a propagation step | Never a propagation step |

Selection rules:

- **Function:** the selected function is the seed. Resolved call chains can reach other
  functions (or supported source scopes evidenced by the graph).
- **File:** the file plus its graph-defined functions are independent seeds. File import/
  include chains and cross-file call chains are both reported, with their types preserved.
- **Component:** its actual immediate member files and their defined functions are seeds.
  Other seed members are excluded from reachable-result counts. Relationships within
  the seed set have separate counts and evidence, including recursive calls.
- **Directory:** recursively follows retained CONTAINS membership, then expands file
  definitions. This includes descendant directories; it differs from direct-member
  architecture components. Missing graph members are explicit coverage issues.

Membership expansion occurs **only at the origin**. Reaching a function does not
implicitly reach its entire file, and reaching a file does not imply all its functions
are affected. There are no invented membership bridges between semantic hops. Files
and components represented by reached functions are mapped for summary/navigation,
not inserted as additional propagation steps. An import is evidence of a static
reference, not proof that a particular imported function is called.

Example: if `entry → load → parse` are resolved CALLS edges, selecting `parse` at two
hops reaches `load` directly upstream and `entry` transitively upstream. The traversal
chain is `parse ← load ← entry`; source evidence still says `entry → load → parse`.
Selecting `entry` downstream follows that latter direction. No runtime order is inferred.

## Traversal and explanation

Deterministic multi-source breadth-first search runs independently per direction.
Seeds and adjacency are sorted by stable IDs. The default depth is one; controls offer
one, two or three semantic hops. Visited sets prevent infinite cycles and deduplicate
entities within each direction. Seeds are never counted as newly reached entities.
The same entity can occur in both directions; distinct summary counts deduplicate it.

Each result contains `id`, `side`, `distance`, `node_path`, `edge_path` and
`other_paths_observed`. Paths start at an actual member seed, not an invented edge
from a component to a function. One deterministic shortest representative is retained.
The alternate-path flag means another route was observed during the bounded search;
false does not establish that no other route exists. Paths are not exhaustively
enumerated. `revisited_edges` includes merges and recursion, not just cycles.

Copied original edges retain source/target IDs, type, reference, source occurrence
count and bounded original source locations. The panel presents original directed
arrows even when the query traversed them in reverse. Each path-step button can make
that actual entity the next origin. Relationships internal to the seed membership
are inspectable separately, rather than misreported as external impact.

## Output, counts and export

`impactExplorer.result` is a serializable query snapshot, schema `1.0`, containing:

- Origin ID, normalized depth/direction, bounded seeds and membership work count.
- Direction-specific reachability records and their original representative edges.
- Bounded `internal_edges` and attributable unresolved/ambiguous/dynamic references.
- Summary, coverage and exact applied limits.

Summary counts separate direct/transitive upstream and downstream results. Distinct
functions, defining files, components, hotspot functions and genuinely scored C
functions are measured over retained reached entities, excluding seeds. Cross-component
pairs count unique directed boundaries on retained representative paths, not every
possible dependency. Internal seed edge/occurrence counts describe observed scans.
Reference counts cover original seed and discovered-node sources before byte trimming;
they are not repository-wide unresolved totals. Output records may be fewer than visited
records after serialization bounds; both counts remain explicit.

Existing FastAPI analysis responses and their schemas remain unchanged. The existing
browser JSON export preserves the complete response and adds optional `blast_radius`
when a query is selected. Clearing focus removes this field on the next export. This
is a single query, not a fabricated repository-wide impact prediction. Raw API consumers
can run the reusable JavaScript engine against the same response; for example:

```javascript
const impact = require('./app/static/impact/engine.js');
const analysis = require('/absolute/path/to/codebase-analysis.json');
const index = impact.index(analysis.knowledge_graph, analysis.architecture, analysis.structural);
const candidates = impact.search(index, 'parse', 'function');
if (candidates.length) {
  console.log(impact.query(index, candidates[0].id, {depth: 2, direction: 'upstream'}));
}
```

## Interaction and presentation

The event-driven SVG canvas fixes the origin at the center, upstream layers on the
left and downstream layers on the right. Each hop has deterministic spacing; function,
file and directory/component shells use different corner cuts. Upstream links use
rose and downstream links muted teal/dashes; arrowheads always retain source direction.
There is no force simulation or animated background. Selecting a record highlights
its retained visible path without recomputing the layout or changing pan/zoom.

The canvas bounds each side/hop to five results. If a predecessor is outside that
subset, its connection is omitted rather than replaced by a false shortcut. All
retained results are available in the searchable, paginated evidence list below.
Selection there opens the full chain even when it is outside the canvas. Canvas and
query bounds are separately disclosed. Dense multi-hop views may require zoom.

Controls support entity-type search, depth, direction, pan/zoom, fit/reset and clear
focus. Graph and architecture/heatmap inspection panels can start impact analysis by
stable ID. The impact panel links back to retained graph entities, component architecture
and file heatmaps. Changing origin/depth/direction uses the current snapshot, never
reingestion. Related paths and source evidence are scrollable; labels have full title
text. Tab/Enter and keyboard viewport navigation reuse the existing SVG viewport.
Reduced motion avoids animated scrolling/transitions. Initial and cleared views have
a compact origin prompt rather than an empty full-height diagram.

## Limits, coverage and security

| Resource | Default limit |
| --- | ---: |
| Membership entities examined | 3,000 |
| File/function seeds | 128 |
| Discovered records across both directions | 400 |
| Adjacency edges examined across both directions | 2,500 |
| Semantic hop depth | 3 |
| Attributable reference records | 100 |
| Internal seed edge samples | 32 |
| Source evidence locations per copied edge | 3 |
| Compact serialized query JSON, UTF-8 | 262,144 bytes |
| Canvas records | Up to five per side/hop, at most 30 plus origin |
| Origin search hits / evidence-list page | 30 / 12 |
| Query cache per repository | 12 |

Limits live in `ArchaeologistImpact.LIMITS`. Both directions share work budgets;
upstream runs first, so severe truncation can leave less downstream work. Selecting
one direction dedicates the budget to it. Serialization drops references, internal
edge samples, then tail reachability records until within budget; representative
edges and summaries are rebuilt. Resource issues explicitly mark partial query output.
Original backend graph and architecture coverage are independently retained. Missing
function owners/components reduce mapped summary counts; no synthetic ownership is
created. Excluded repository files and unresolved runtime behavior remain unknown.

Index construction is linear in retained input plus deterministic sorting. Searches
are debounced over retained entities. Hover does not traverse graphs. Query results
are cached with a bounded per-repository lifetime; selection reuses SVG elements.
A new origin/depth/direction rebuilds a small bounded composition. Replacing a repository
clears caches/selections and destroys SVG listeners, observers and queued frames. The
shared viewport now namespaces marker IDs so architecture and impact canvases coexist.

Repository-controlled text is inserted through textContent, not HTML. No network request,
source execution, dynamic import, package installation or deserialization is performed
by this engine. Existing upload, GitHub, parsing and trusted-model security controls
remain in place. No graphics dependency or WebGL context is added. No FPS or measured
smoothness claim is made.

## Engineering context and limitations

Complexity is calculated source structure. Hotspots reuse existing rule-based reasons.
Only graph-linked C functions with actual analyzed model output receive score context;
Python and missing-model nodes remain unscored. Scores are uncalibrated research
estimates, not impact probabilities or confirmed vulnerabilities. No averaged file/
component risk or invented severity is introduced.

Static resolution limitations from the knowledge graph apply, including dynamic dispatch,
macros/function pointers, ambiguous imports and missing build context. Membership is
bounded and only retained definitions participate. Directory components are structural
groupings, not proven runtime architecture. No test execution, runtime tracing or actual
breakage prediction is performed. These are potential review candidates only.

## Verification

The complete regression suite passed **385 Python tests, 0 failed, 0 skipped**.
This includes four impact checks (the real ZIP check runs with and without the model),
which exercise **32 browser-free impact cases** plus a real-response smoke case per
model configuration. Existing architecture (9) and graph (24) frontend cases also pass
through their original runners; Node cases are not additional Python tests. One existing
Starlette/httpx deprecation warning remains. JavaScript syntax and dependency consistency
checks pass. The automated fixtures exercise upstream/downstream semantics, depth, calls/imports/includes, separate
membership, recursion, alternate paths, unresolved references, nullable ML context,
resource/UTF-8 budgets, deterministic output, path evidence, bounded layout, safe text,
state cleanup, cached queries and ID-based navigation. Python integration tests pass a
real mixed C/Python ZIP through the existing analysis endpoint, then run this same
Node engine against its actual response and trusted model output.

The actual eight-file mixed C/Python ZIP produced one upstream caller for the C helper,
two upstream entities for the Python helper file (one call, one import), and one downstream
include dependency plus one internal call for the native component. The trusted local
model analyzed both C functions. Repeating ingestion with the artifact unavailable
preserved those structural results with zero scored reached functions. The research model was not
retrained and held-out evaluation was not repeated.

Chromium startup was attempted in this sandbox and failed with
`setsockopt: Operation not permitted` (exit 133). No visual, responsive, console or
interactive browser verification is claimed. The deliberate engineering/design review
checks data direction, geometry bounds, event paths, label truncation/full text access,
keyboard controls, scoped responsive CSS and evidence availability; it cannot substitute
for opening the page. No live GitHub request was needed or verified for this feature.

Local checks:

```bash
source .venv/bin/activate
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
# Separate terminal, repository root:
node tests/frontend/impact.test.cjs
pytest tests/test_impact.py -q -s
pytest -q
```

At `http://127.0.0.1:8000`, upload a known mixed-language ZIP. Select a callee, compare
one/two/three-hop callers with source, switch direction and inspect each original arrow
and source location. Try file/component/directory origins; check internal membership
edges and distinct counts. Search an off-canvas result, follow a path, change origin,
then navigate to the graph, component and heatmap. Launch impact from those views.
Verify clear/export, repository replacement, an unsupported-language repository and a
missing model. Check zoom/pan and keyboard controls at 1366×768 and mobile widths,
including reduced motion and long names. Record browser profiling before making any
performance claim. Academic reports remain unchanged until Task 7.

## Explain an investigation with Jordan

The impact inspector's Ask Jordan action preserves origin, selected depth/direction and,
when applicable, the selected reachable target ID. Jordan reconstructs the representative
path using this engine, preserving original relationship arrows/evidence. Only compact
IDs/options cross workspace navigation; no source parsing or network call occurs on
handoff. Optional cloud explanation requires a separate reviewed disclosure and consent.
See [Jordan evidence and privacy](jordan.md).
