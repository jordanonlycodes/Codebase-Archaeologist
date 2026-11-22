# Task 7B — starting baseline

## Repository and handoff

Started on `main` at `dbb408c0a3389c2127518f622f4ad9ae532c62ee`.
Local `origin/main` equals HEAD (zero outgoing commits before this task); this is not
fresh remote verification. No tracked changes. Three existing user-owned untracked
files remain: `app/static/vendor/3d-force-graph-1.73.3.min.js`, its `.LICENSE`, and
`graph-assets.json`. They are neither deleted nor staged.

Read the Task7A audit, evidence index, demo checklist, progress and compliance summary.
Task7A recorded 506 passing tests, a corrected inclusive score >=0.5 threshold,
trusted-local model prerequisites, incomplete browser acceptance, and stale report
source hashes. The user's Task7B confirmation supersedes the historical group question:
Bilal Malik (24P-3061) and Aun Anis (24P-3017), instructor-permitted two-member group.
No independent institutional document is implied by this user confirmation.

## Relevant architecture

`app/main.py` mounts FastAPI routes and static assets. `app/routes/dashboard.py`
renders `/`, `/explore`, and nine independent workspaces: overview, risk, structure,
graph, architecture, heatmaps, blast-radius, jordan, time-machine. Feature-specific
Jinja includes and lazy assets share `workspace_base.html`, `product/design.css`,
`product/common.js` and `product/workspace.js`. `product/store.js` owns source-free,
per-tab IndexedDB snapshots (2 hours, three rows, 24 MiB each). No server-global active
repository is introduced. ZIP/GitHub intake share bounded analysis; ML loading and
inference remain in `app/ml/`, with supported C functions only. The graph has shared
indexes/layouts and SVG/Three adapters. History REST retrieval uses bounded process
caches, token-scoped keys, singleflight and explicit rate-limit classification.

Tests: Python `tests/`, deterministic Git fixtures and frontend Node harnesses in
`tests/frontend/`; the Python suite invokes those harnesses. No npm install required.

## Baseline commands and environment

Run from the project root. The ordinary documented command is `.venv/bin/python -m
pytest -q`. This sandbox requires the existing process-local selector workaround:

```python
import selectors, pytest
Base = selectors.DefaultSelector
class Polling(Base):
    def select(self, timeout=None):
        return super().select(.02 if timeout is None else min(timeout, .02))
selectors.DefaultSelector = Polling
raise SystemExit(pytest.main(['-q', '--tb=short']))
```

Actual baseline: **506 passed, 0 failed, 0 skipped in 89.13 seconds**, one existing
Starlette/httpx deprecation warning. No application networking
code is changed for this environment workaround.

Fresh environment attempts: Chromium headless `--dump-dom about:blank` exited133
before rendering (`setsockopt: Operation not permitted`); Uvicorn completed startup
but could not bind127.0.0.1:8000 (exit3); direct `curl --noproxy '*' -I
https://api.github.com` failed DNS (exit6). Thus no browser/GPU/live GitHub success,
website screenshots or responsive visual verification is claimed.

## Confirmed inspection targets

3D initial fitting currently depends on scene geometry immediately after asynchronous
library graph updates. Hidden containers are sized with arbitrary fallback dimensions.
Only damping is explicitly configured; pan gestures are undocumented in the visible
controls beyond small help text. Resize does not reframe an initially fitted camera.
Investigate/fix these without changing graph extraction, ML or idle rendering policy.
The existing symbol is a stacked-layer mark, not the approved Dependency Relic.
No approved image was found in the repository initially. During Task7B the user
supplied a reference image and explicitly selected its left-hand Minimalist Relic.
Use that reference for an editable SVG interpretation, not a textured recreation.
