# Task7B.1 — local motion acceptance

New effects require a new human review; previous7B acceptance does not certify them.
Record PASS/FAIL, fixture/snapshot, browser/version, viewport and any console errors.

## Startup and genuine data

```bash
cd /home/jordan/Projects/codebase-archaeologist
source .venv/bin/activate
python -m pip check
python - <<'PY'
from pathlib import Path
from zipfile import ZipFile
root=Path('tests/fixtures/university_demo')
with ZipFile('/tmp/codebase-university-demo.zip','w') as z:
    for name in ['review.c','helpers.py']: z.write(root/name,name)
PY
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000/ then /explore; upload the generated ZIP. Restore trusted
model files/environment as documented in task7b_manual_demo_checklist.md if unavailable.
Do not retrain or configure a cloud provider for this task.3D needs the existing local
vendor bundle; missing bundle must fall back honestly to2D. See7B vendor licensing notes.

## Normal motion —1366×768 first

| Check | Expected | PASS/FAIL / notes |
|---|---|---|
| Landing and import | Existing hero/logo intact, controls respond immediately, genuine errors enter without shaking or fake progress. | |
| Overview | Actual summary cards reveal in a short sequence; four integer metrics finish at true values.2files/4structural functions in original fixture; completion is not delayed. | |
| Return to Overview | Browser back/forward/refresh and workspace links retain snapshot. Counts do not repeatedly restart within retained motion preferences; no reanalysis. | |
| Risk / Structure | Existing actual C predictions/metrics, search/filter/details still work; no animated ML probabilities or invented values. | |
| Graph2D | One subtle entrance, select/search/neighborhoods/filters work during it; no new layout jump or simulated edges. | |
| Graph3D | Genuine WebGL: rotate, zoom, right/Ctrl-drag pan, left-pan toggle and viewport arrow keys; Fit/Reset View center correctly; dragged nodes persist on reset. | |
| Camera focus | Select entity then Focus selected: composed transition preserving viewing direction; user movement remains usable. Test empty/single/disconnected views, resize/fullscreen. | |
| Architecture | Actual directory components gently assemble and existing links trace once. Select components/edges, inspect source, pan/zoom; no reordering for motion. | |
| Heatmaps | Cells reveal briefly on directory entry. Hover/keyboard focus are clear; all six metric colors/legends remain honest. No color morph implying changing risk. | |
| Blast Radius | Select sum_values: actual entry caller/path appears upstream. Select its evidence: trace follows only that relationship. Stable final layout, no endless pulses or guaranteed-breakage claim. | |
| Jordan Local | Ask overview and Who calls sum_values?: only latest actual answer enters, text is immediately selectable. Older turns do not reanimate. Cite evidence, open details and start new conversation. | |
| Jordan state | Local instant answers do not linger in fake thinking. Setup checking status clears; unavailable Enhanced stays honest; no external request without consent. Do not activate providers. | |
| Snapshot replacement | Analyze Python-only ZIP, then restore demo: no stale counts/messages/reveals. Python has no C-model predictions. | |
| Navigation / keyboard | Active workspace indicator/refined focus, native back/forward and scroll restoration; no overlays, focus traps or delayed clicks. | |

## Time Machine — only real public GitHub history

Use another tab and a small public GitHub repository or the project's actual URL.
Network/quota must permit retrieval. Ordinary ZIP must show no-history, not demo commits.

- [ ] Timeline markers/activity plot reveal finite real values; zoom/pan/FitHistory and
      keyboard selection stay usable during/after entrances. Date/order labels remain.
- [ ] Commit selection updates actual details, not viewport reset or fake interpolations.
- [ ] Churn metric/directory navigation is immediate, accurate and visually restrained.
- [ ] Compare two actual revisions: summary fades; additions/deletions remain real values.
- [ ] Evolution scrub/loaded-only playback is responsive; no repeated reveal wave every
      playback frame or extra request triggered by motion. Pause works.
- [ ] Cancel a genuine in-flight tree/compare/load; activity mark stops, old evidence
      remains. Simulate offline/failure: clear message and no stuck status/spinner.
- [ ] Repeat cached comparison/tree selection; request counts remain unchanged as before.

## Reduced motion — mandatory

In browser DevTools emulate prefers-reduced-motion:reduce or enable OS Reduce Motion.
Reload each page with the same snapshot, then also toggle preference while a reveal is
running. Record both initial and live-preference behavior.

- [ ] Counters show final formatted values immediately; no count-up, hidden data or delayed interaction.
- [ ] Card/cell/line traces and decorative transitions stop; genuine focus/selection stays visible.
- [ ] Graph focus/Fit use0ms transition on subsequent actions; pan/zoom/reset still work.
- [ ] Jordan text/evidence appears immediately; pending operations use static status/dot.
- [ ] Time Machine has no entrance stagger and playback respects existing reduced preference.
- [ ] Hide tab mid-count/reveal/request, then return: accurate final text, no stale reveal,
      background perpetual animation or discarded data. Busy reflects actual request only.

## Responsiveness, lifecycle and accessibility

Repeat at1440,1024,768,390 and320px widths. No page overflow, offscreen translation,
clipped toolbar, microscopic controls or logo misalignment. Narrow reveals travel less;
important labels/actions remain available without hovering. Test touch where hardware
permits; do not claim it from desktop simulation alone.

Navigate between graph/architecture/heatmap/impact/Jordan/history10times; replace repository.
Check no duplicate canvas, observer-driven resurrection, stale state, listener accumulation
or new fetch on harmless rerender. On DevTools Performance, optionally record **actual**
long tasks/paint/idle behavior; do not infer FPS improvements from implementation alone.

Keyboard: visible focus, links/buttons/details usable immediately; screen reader receives
only final metric values, not intermediate counts. No focus trap or flashing. Browser
console/network must show no missing motion/brand assets or unsafeHTML errors.

Capture authentic normal desktop and mobile stills after motion settles; optional short
screen recording can document actual transitions. Do not use generated mockups or claim a
still screenshot proves smooth performance. See docs/screenshots/README.md.

## Local regression commands

```bash
python -m pytest -q
node tests/frontend/motion.test.cjs
node tests/frontend/graph.test.cjs
python -m pytest -q -s tests/test_product.py
```

Last command supplies genuine source/Git fixtures to actual-document frontend harnesses.

Acceptance record: date____ reviewer____ browser____ SHA____ viewport____
Normal____ reduced____ repeated navigation____ failures/recordings____
