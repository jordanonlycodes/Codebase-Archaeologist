# Task7B.1 — motion baseline

Starting main/HEAD:460736e4d63f92598e509f720fa442f6de5d99b8. Tracked tree clean;
three pre-existing vendor assets remain untracked and untouched (3d-force-graph bundle,
LICENSE, graph-assets.json). No logo, model, source-analysis or API change planned.

Read Task7B test report, manual checklist,7C handoff and brand identity notes. The user
reports successful local7B operation; that is not verification of new7B.1 motion.

## Actual architecture and existing motion

FastAPI renders public landing/import plus nine separate workspace documents: overview,
risk, structure, graph, architecture, heatmaps, blast-radius, jordan, time-machine.
workspace_base.html owns shell/assets; product/workspace.js restores per-tab expiring
IndexedDB context, hydrates one feature, cleans it up on pagehide and resumes BFCache.
Ordinary anchors/history remain native; no SPA router or page-capture overlay is needed.

Existing design.css defines short --fast/--ease transitions and a400ms workspace entrance;
landing has CSS editorial reveals and an offscreen/visibility-paused24Hz canvas. Graph
SVG reuses nodes and schedules pointer work;3D has fixed layout,250ms fit/300ms focus,
bounded DPR/MSAA-off/idle pause and scoped pan controls. Architecture/impact are event-driven
SVG scenes with short fill/stroke selection transitions. Heatmap values/colors are real
measurements. TimeMachine timeline is event-driven with selection transitions and cached
history requests; Jordan synchronously answers local queries and currently reanimates
rebuilt conversation articles with a180ms CSS entrance. No new dependency is necessary.

Existing accessibility: skip links, names, visible focus, scoped viewport keys, native
details, reduced-motion CSS, no-source snapshots and text-safe labels. JS camera duration
is reduced-motion aware at construction; dynamic preference changes need consideration.

## Baseline verification

Full suite: **508 passed,0failed,0skipped in94.24s**, one existing Starlette/httpx warning.
Command from project root is normally `.venv/bin/python -m pytest -q`. This environment
requires the same process-local selector wrapper as7B (no runtime app patch):

```python
import selectors, pytest
Base = selectors.DefaultSelector
class Polling(Base):
    def select(self, timeout=None):
        return super().select(.02 if timeout is None else min(timeout, .02))
selectors.DefaultSelector = Polling
raise SystemExit(pytest.main(['-q', '--tb=short']))
```

## Implementation opportunities / boundaries

Use a small native motion utility with finite Web Animations and bounded RAF counters;
explicit semantic renderer hooks, one-shot visibility observation and complete teardown.
Keep final values immediately available to assistive technology, and suppress/cancel
motion on reduced preference, pagehide or document hiding. Never modify evidence colors,
layout positions, graph relationships, ML estimates, histories or data-fetch lifecycles.
Only overview integer counts may count visually; ML/risk/historical scores do not.
Avoid replay on ordinary filter/hover refresh; preserve seen keys per tab/snapshot with
small TTL/entry bounds. Without native animation support, render final content normally.

Previous sandbox Chromium socket/localhost restrictions remain known possibilities;
fresh browser/startup attempts will be recorded. No new visual acceptance or measured
FPS is implied by baseline tests. Six required7B.1 documents will record final work.
