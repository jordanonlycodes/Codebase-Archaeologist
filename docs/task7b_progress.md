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
