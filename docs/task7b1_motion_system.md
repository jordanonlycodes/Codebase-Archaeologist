# Task7B.1 — shared motion system

## Principles and implementation

`app/static/product/motion.js` owns finite native Web Animations, bounded overview
integer counters and one-shot IntersectionObserver reveals. `motion.css` owns the
shared interaction vocabulary; existing feature renderers explicitly request effects
at semantic data/selection boundaries. No polling, mutation observer, route interception,
physics restart, new framework, fetch, source parsing or backend change is involved.
Content is present before/during effects. Unsupported APIs leave final content visible.

Timing tokens:160ms feedback,340ms normal reveal,560ms significant reveal,45ms stagger
(capped220ms). Easing cubic-bezier(.22,1,.36,1). SVG group entrances animate opacity
only, preserving positional transforms. Relationship traces are finite on actual paths,
restore original dash/style after finishing, and never imply runtime execution order.

No global initial-opacity-zero stylesheet or delayed interaction. Focused content is
not animated. Native details remain native; their contents receive a short visual
entrance without intercepting keyboard, opening or focus. Native document navigation,
browser scroll restoration and BFCache are retained.

## Accessibility and performance boundaries

Reduced motion is checked in CSS and JS. Live preference changes and document hiding
cancel animations, settle counters and disconnect pending observers. No intermediate
counter value is exposed to assistive technology: the exact final formatted number is
in an sr-only span; only the aria-hidden visual span changes. On finish/cancellation,
original final text is restored. Missing/fractional/negative/nonnumeric values are not
counted; C-model probabilities and historical values never count. Effects do not change
the analysis response, color scale, source evidence, node positions or IDs.

At most24 native effects,12items per batch/trace/observed group,4counters, and capped
delays. No independent item timers. Frame callbacks exist only during finite counters;
completion/hide/reduced preference/pagehide cancels them. Hidden-document CSS activity
is paused. Metric formatting uses the existing formatter and safe text nodes only.

Seen reveal keys are scoped by per-tab snapshot ID/page, capped80entries, each expiry
bounded by the snapshot's expiry and2hours. Only small visual preferences are added to
sessionStorage, never analysis payload/source/provider content; failures are optional.
A return to the same page/snapshot does not replay counters. A new snapshot has its own
scope. Lifecycle destroy removes media/visibility listeners, observers, animations and
frames; begin safely destroys any previous lifecycle and can resume BFCache.

## Verification checkpoint

Primitive tests:11Node cases pass for final values, reduced motion (including live
change), hiding, cancellation, observer release, repetition, bounds, safe fallback,
focus and genuine busy flags. Browser appearance/performance acceptance remains separate.
Integration results and final matrix are in the accompanying7B.1 documents.

## Shell / overview integration checkpoint

Public/workspace shells load the small shared CSS; only workspace loads the JS.
workspace.js begins motion with the restored snapshot ID/expiry, destroys on pagehide,
and begins a fresh lifecycle on BFCache resume. The old whole-workspace CSS animation
is removed to avoid double entrances; headings/nav receive finite CSS emphasis.
Overview observes at most12actual summary cards and visually counts four genuine integer
metrics once per retained tab/snapshot. Completion badge reveal is not a loading state.
No result or provenance is fabricated. The existing landing composition is preserved.
Focused primitive+actual-document integration: **21Python tests passed,0failed/skipped,
41.33s**, one existing deprecation warning. Browser-free verification only.

## Visualization checkpoint

Graph mode entrance is one opacity reveal per renderer mode/snapshot; entity inspectors
reveal on selection.3D focus450ms/fit340ms preserve direction and use the current reduced
preference (zero duration). Existing pan/reset/resize/data/quality/idle behavior remains.
Architecture component groups and real dependency paths receive bounded opacity/line
reveals; heatmaps reveal a bounded group on directory/area changes, with metric colors
updated directly, never decoratively interpolated. Impact reveals real retained nodes
and paths once per origin/depth/direction; picking a result traces only its actual path.
Dimmed relationship opacity is preserved during effects, not temporarily brightened.

Primitive12cases, graph26cases, architecture10cases, impact32cases pass. Focused actual
product/graph/motion Python suite **27passed,0failed/skipped in44.91s**, one existing
warning. Native GPU/visual acceptance is still unavailable: fresh Chromium exit133 at
setsockopt and Uvicorn exit3 at localhost binding, before any website rendering.
