# Task 7B — recovery and verification record

## Checkpoint 1 — baseline and inventory

Inspected Task7A handoff, current main/HEAD, routes, snapshot lifecycle, C-only model
integration, graph adapters/tests, local font licenses and user-owned vendor receipt.
No tracked user edits. Origin tracking matches HEAD; network freshness unverified.
Baseline full pytest: **506 passed, 0 failed/skipped, 89.13s**, one existing
Starlette/httpx warning, using the documented sandbox polling selector.
Chromium exits133 before rendering; localhost bind exits3; GitHub DNS probe exits6.
No website screenshots or measured FPS. Two-member confirmation is supplied by the
user; current project identity will be corrected, old report revision deferred to7C.

Next: finish baseline, commit this checkpoint; test and fix camera fit/controls;
create SVG brand system and targeted asset/route tests; run broad regressions and
real local-model mixed ZIP smoke; complete required test/demo/7C handoff documents.
Do not stage the three untracked vendor assets: redistribution review remains open.

The user subsequently supplied a three-concept logo reference and selected the
left-hand Minimalist Relic. Branding follows that explicit direction.

## Checkpoint 2 — camera fixes

`graph/three.js`: coordinate-based bounding-sphere fit replaces a race-prone immediate
scene bbox query; real width/height only, aspect-aware fit, no fabricated hidden sizes.
Fitted resize reframes; user camera navigation is retained after manual interaction.
Reset restores orientation and fits without relayout. Explicit supported OrbitControls
pan/rotate/zoom/screen-space settings, scoped keyboard listeners, control-event wakeups
and complete cleanup. `graph/explorer.js` and graph template add a pressed-state left
pan toggle, focusable viewport and clearer gesture/reset instructions. No source-analysis
or ML changes. MSAA-off, bounded DPR, geometry reuse and idle rendering remain.

Extended the actual 3D adapter harness for translated/disconnected/single/empty bounds,
aspect resize, hidden hosts, navigation preservation, reset stability and listener
cleanup; added a pan-toggle lifecycle case. New harness against original adapter fails
at coordinate fitting; patched harness **25/25 passes**. Focused Python graph/product
suite **25 passed, 0 failed/skipped in38.47s**, one existing warning. These are browser-free
checks, not physical camera/visual acceptance. See knowledge_graph.md for usage.

## Checkpoint 3 — Minimalist Relic branding

Received the actual user reference and explicit Minimalist Relic preference. Authored
editable geometry and local OFL serif outlines via tools/generate_relic_assets.py;
dark/light symbols and wordmarks, simplified mark, favicon and touch icon. Integrated
public/workspace navigation and favicon metadata; retained previous mark.svg URL.
Rendered/inspected actual vector assets with librsvg (dark/light,16/32/64px), not a
website screenshot. Two asset/shell regressions plus existing product suite:
**21 passed, 0 failed/skipped in43.37s**, one existing warning. No new runtime dependency.

README now names both confirmed members; submission README explicitly labels its old
individual wording historical and defers the real report correction to7C. Brand/legal
notes document reference use, OFL attribution and limited name research: other products
use this name, so no name/logo exclusivity or trademark clearance is asserted.

Small source review correction: mobile repository action row did not wrap (three real
actions could exceed narrow screens); add wrap and compact <=420px workspace lockup.
These CSS safeguards are inspected/testable source changes, not visually certified
responsive layouts. A fit requested on a hidden 3D host now persists until measurement;
the new assertion passes. Inference API text now reflects7A's inclusive0.5 convention.

## Checkpoint 4 — core and feature regression

Actual mixed ZIP smoke with original tracked review.c/helpers.py ran real parsers and
selected local model:2files,24physical lines,4structural functions,7nodes/7edges,
3Cpredictions (.6446299251115485/.4640631119969904/.44115041436869545); Python unscored.
Python-only, JS-only and malformed-C states plus empty/invalid/traversal ZIP and invalid
GitHub URL were exercised. An initial ad-hoc script expected400 for invalid GitHub URL;
422 is the genuine existing contract; corrected the script expectation, no app change.
All11 public/workspace pages200. Jordan Local on this actual response correctly answered
summary, complexity, callers and1-hop change impact using the entry→sum_values edge.
No provider configured/contacted; capability check shows cloud unavailable honestly.

Read-only academic audit passes: source/class counts,113cleaning decisions, prepared
matrices/schema/features, training-derived imputation/scaling, three candidate digests
and selected pipeline checksum. No benchmark fit/evaluation/report regeneration.
Report validator reproduced exit1 at known stale app/ml/repository.py hash; six old source
paths remain listed in7C handoff. Output report hashes still match, not bypassed.

## Checkpoint 5 — responsiveness, safety and quality review

Reviewed navigation sizes, context actions, graph controls, labels, focus/reduced-motion,
lazy assets, source-free storage lifecycle and renderer cleanup. Narrow action wrap and
compact brand safeguards are included; actual responsive geometry requires local browser.
3D fitting stays bounded by existing retained graph view, no relayout on camera reset;
control events/listeners clean up, MSAA-off/DPR/idle policy preserved. No FPS claim.
Brand SVG XML checks and local render review are complete; site renders are unavailable.
Vendor bundle digest unchanged; MIT text matches pinned upstream. Transitive notice/
independent archive review still needed; all three original assets remain untracked.
Limited public name research found other products: no trademark/visual clearance claim.

## Checkpoint 6 — final automated results and handoff

Full post-change suite **508 passed,0 failed,0 skipped in96.58s**, one existing warning.
This includes existing Python and frontend runners; do not add Node cases to508.
Explicit graph harness25/25passes; earlier focused graph/product25passes and newbrand/
product21passes. Syntax checks pass all28 non-vendor applicationJSfiles. pip check passes.
Required six Task7B documents produced; manual acceptance and7C handoff distinguish
verified API/harness results from blocked browser/liveGitHub/clean-machine checks.

Checkpoint commits:99c3067 baseline, a9ee5c4 camera, e7ae0b0 branding/identity.
Final documentation commit follows this review; no user vendor file staged. Normal
push will be attempted and its actual result recorded. Next task7C may use real saved
scientific evidence and new assets; first complete local browser/demo signoff. No7C
report generation or optional roadmap/cloud work started in this task.
