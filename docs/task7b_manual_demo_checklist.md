# Task7B — local Ubuntu browser/demo acceptance

Run as Bilal/Aun on the actual presentation machine. Record date/browser/OS/display,
Git SHA and PASS/FAIL for each item. Automated checks are not substitutes for this list.

## 1. Environment and trusted prerequisites

```bash
cd /home/jordan/Projects/codebase-archaeologist  # adapt checkout path on Ubuntu
source .venv/bin/activate
python --version
python -m pip check
sha256sum artifacts/devign-v1/pipeline.joblib
```

For a clean environment create `.venv` with compatible Python and install requirements:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt -r requirements-ml-frozen.txt
```

The trained artifact records **Python3.14.10**, sklearn1.9.1,numpy2.5.5,scipy1.18.1,
joblib1.6.0,tree-sitter0.25.2/tree-sitter-c0.24.2. Do not assume Ubuntu's default Python
or a fresh broad-range install can load it. Resolve compatibility in7D before the demo.
Restore **trusted** `pipeline.joblib`, `metadata.json`, `feature_schema.json` together
under artifacts/devign-v1 (or operator-only ARCHAEOLOGIST_MODEL_DIR), never from an upload.
Expected pipeline SHA256:
`9988945c6c851e885f3942a406a4d6c7d704547797e266d6d0aed95520db74e6`.
Raw benchmark data is unnecessary for inference. No provider API key is needed.

3D needs the local pinned bundle `app/static/vendor/3d-force-graph-1.73.3.min.js`.
On a trusted developer machine `python tools/install_graph_assets.py` downloads it;
review license/provenance notes in vendor README before distributing. Do not blindly
publish the three currently untracked vendor files. If absent, expect honest2D fallback.

```bash
python - <<'PY'
from pathlib import Path
from zipfile import ZipFile
root=Path('tests/fixtures/university_demo')
with ZipFile('/tmp/codebase-university-demo.zip','w') as archive:
    for name in ['review.c','helpers.py']: archive.write(root/name,name)
PY
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open **http://127.0.0.1:8000/**. No cloud configuration/browser flags required. Do not
disable security to make a feature work. Use the original, unlabeled demo code above.

## 2. Core user journey — record PASS/FAIL

| Check | Expected | Result / evidence |
|---|---|---|
| Landing and import | Relic visible/readable, no404 assets, existing hero intact; favicon present. Keyboard reaches skip/navigation/import. | |
| ZIP picker/drop | Select generated ZIP; real progress wording, no invented analysis percentages. Cancel an upload, retry and complete. | |
| Overview |2files,4C/Python structural functions; repository name matches this ZIP; context survives all workspace links/back/forward/refresh. | |
| Risk |3actual C predictions, ~.644630/.464063/.441150; one class1; no Python scores. Labels are research estimates, not confirmed defects. | |
| Structure |clamp_index complexity3, sum_values2, entry1, describe_count2. Search/sort/details and graph/impact navigation retain exact IDs. | |
| Graph2D |Hierarchy/calls/dependencies controls;7nodes/7edges overview. Calls includes entry→sum_values. Search/filters/overlays/selection/fit/zoom/drag usable. | |
| Architecture |Root component reflects2member files/4functions; inspector uses actual evidence, empty inter-component state honest. | |
| Heatmaps |Switch all six metrics; size/color legends correct, Python unscored for ML, breadcrumbs/drill-down/reset work. | |
| Blast Radius |Choose sum_values, upstream1hop shows entry. Direction toggles/depth1–3/paths/evidence work; no guaranteed-breakage claim. | |
| Jordan Local |Ask overview, most complex, Who calls sum_values?, What could be affected if I change sum_values? Evidence links match actual entities. New conversation clears history. | |
| Jordan mode |Local visibly active; Enhanced click explains unavailable configuration accessibly. Do not enable/configure cloud for this task. | |
| ZIP Time Machine |Explains no genuine Git history; no fake timeline/churn. | |
| Export |Export twice; parse JSON, counts/scores match; no raw source/local paths; names/MIME reasonable. | |
| Persistence |Same-tab navigation/refresh retains context; new independent tab no unwanted context. Forget removes active snapshot; a new upload clears stale selections. | |

## 3. Specific3D camera acceptance — essential

Use1366×768 first, then1440/1024/768/390/320px widths. Record actual viewport sizes.

- [ ] Select3D; one WebGL canvas, graph initially centered and visible, labels readable.
- [ ] Drag **empty canvas** to orbit360°; scroll to zoom; nodes remain selectable.
- [ ] Right-drag or Ctrl+left-drag empty canvas pans/changes camera target. No pagewide
      scroll interception. Toggle **Pan with left drag**; pressed state visible; left-drag
      empty canvas translates. Toggle off; left-drag orbits again.
- [ ] Tab to viewport; arrow keys pan only while viewport focused. Search/toolbar keys
      remain normal. Two-finger touch pan if available; do not claim touch if not tested.
- [ ] Fit recenters whole displayed graph. Reset View restores frontal direction and
      fits after orbit/pan/zoom; dragged node positions are not discarded.
- [ ] Resize/window/sidebar/fullscreen: canvas matches parent, initially fitted view
      stays framed; manually adjusted target does not jump merely on resize.
- [ ] Switch all3perspectives,2D/3D repeatedly; selection/filters/overlays remain applicable.
      Choose empty filter, single node and disconnected graph where available; no errors.
- [ ] Hover labels, select via inspector/search, verify edge directions and risk/complexity
      legends. Performance quality remains usable; no measured FPS claim without profiler.
- [ ] Navigate away/back and replace repository: no duplicate canvas/listeners, stale
      selected entity, retained simulation or background rendering. Check browser console.

## 4. Live GitHub/history (only if connectivity and quota permit)

Use a **separate tab** and a small public GitHub repo (or the project's verified public
URL https://github.com/jordanonlycodes/Codebase-Archaeologist). Record actual analyzedSHA.
Import once; open Time Machine. Its recent default-branch window is bounded, not all history.

- [ ] Timeline selects real commits; zoom/pan/FitHistory preserve orientation.
- [ ] Activity dates/counts, churn metric/search/drill-down, comparison base→target
      additions/removals/renames and real patches match evidence; no historical ML claims.
- [ ] Evolution loads actual pinned trees; cached-only playback and stop/scrub work.
- [ ] Repeat comparison/tree selection: cache diagnostics/requests show reuse, not storms.
- [ ] If denied/limited/offline, status explains actual failure/reset/cooldown; previously
      loaded panels remain usable. Do not deliberately exhaust GitHub quota.
- [ ] Navigate to verified current files only; deleted/renamed mappings remain explicit.

## 5. Failure/responsive/accessibility acceptance

- [ ] Invalid/empty ZIP, oversized input and malformed C yield safe recoverable messages.
- [ ] Python-only/unsupported ZIP still gives inventory; no invented C-model predictions.
- [ ] Optional second process with **empty** operator model directory and port8001 shows
      unavailable model while structure/graph still work. Never delete real model files.
- [ ] At all target widths: no page-level horizontal overflow, clipped menu/dialogs,
      hidden actions or unreadable brand; long paths scroll/read accessibly.
- [ ] Keyboard/focus order, visible focus, menu state/Escape, reduced-motion OS preference,
      selected-state contrast and recoverable errors. No hover-only essential information.
- [ ] DevTools console/network: no missingassets, unhandlederrors or frontend tokens.

## 6. Evidence and regression commands

```bash
python -m pytest -q
node tests/frontend/graph.test.cjs
node tests/frontend/workspace.test.cjs
node tests/frontend/architecture.test.cjs
node tests/frontend/impact.test.cjs
node tests/frontend/jordan.test.cjs
python -m pytest -q -s tests/test_product.py
```

The last Python command supplies genuine analysis/history fixtures to the actual-document
product/time-machine Node harnesses. No network needed. Capture real landing, risk,
graph2D/3D, architecture, heatmap, impact, Jordan and history screenshots only after
these browser steps; follow docs/screenshots/README.md. Record fixture, viewport andSHA.

Team acceptance: date________ browser________ SHA________ reviewer________
Open failures________ report screenshot paths________
