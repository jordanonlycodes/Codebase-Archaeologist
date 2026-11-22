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

## History / Jordan / safety checkpoint

TimeMachine timeline markers, monthly plot, real directory maps, comparison balance and
inspectors have finite evidence-keyed entrances. A map's directory/metric key avoids
repeated waves during cached playback. Retrieval busy marks follow existing request/
finally/cancel paths; no extra fetch, cache mutation or retry was introduced.
Jordan reveals only the newest actual turn; rebuilt old/restored turns are static.
Citation/details effects preserve safe text. Local processing is synchronous and clears
busy in finally, without artificial delay; a visible spinner is not guaranteed for an
instant answer. Existing setup/request status gets pending-only feedback, without
configuring or activating any provider. Error/cancellation/teardown clear the marks.

Narrow viewports use3px instead of6px rise and25ms instead of45ms stagger. Removed-view
native effects are pruned before new effects; original empty computed opacity falls back
to1 so detached newly inserted summaries do not disappear.14primitive cases pass.
Actual-document tests now cover motion scope/BFCache, new-message-only reveal, local
error cleanup and history-cancel loaded-state preservation. Focused product+motion run:
**22passed,0failed/skipped in42.99s**, one existing warning. All29appJSsyntax checks pass.

## Checkpoints / final review

8efafee baseline;0b2d133 primitives;c85d95b shell/overview;9c9b866 graph/architecture/impact.
History/Jordan checkpoint follows the successful focused tests above. Final complete
regression and human visual acceptance are recorded separately. No brand SVG, source
analysis, API, model or historical-evidence module was changed. Seen preference eviction
(after80entries) or blocked session storage may permit a later repeat reveal; this is
bounded visual state, not repository retention or correctness state.

## Deliberate second quality pass

Review of delayed Web Animations identified a potential visible-to-dim jump during
stagger delays. Effects now apply their nonzero-opacity first frame **backwards** during
the bounded delay, then release the effect entirely after completion (no forwards fill).
This avoids intentionally scheduling a fully bright frame followed by a delayed fade,
without CSS-hidden content or retained transforms/styles. Regression expectations pin
that fill policy. Primary pressed-button specificity also overrides its hover lift.
These are source/API semantics improvements, not claims of observed browser smoothness.

Final full regression after quality refinement:511passed,0failed/skipped in102.32s;
one existing warning. All216frontend cases pass;29JSsyntax checks pass. Application
performance and cinematic appearance remain unmeasured/unverified in a real browser.
No additional dependency, branded asset change, report generation or provider activation.
