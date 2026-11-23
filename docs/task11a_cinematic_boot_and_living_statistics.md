# Task 11A — Cinematic boot and living statistics

## Scope and release safety

Development branch: `feature/cinematic-experience`. Entry working tree was clean at
`09f6b6df29b6b3e8e81c48c7f8f929a6e638dce5`. Before implementation, verified that `main`
and `v1.0.0-university-release^{}` both pointed to that Task 7E commit. Neither reference,
the release archives, accepted report files nor production model was changed.

The existing graphite/ivory/garnet palette, local fonts and Minimalist Dependency Relic
are reused. Presentation follows actual page loading; no scan/model initialization is
implied by the introduction. No external dependencies or new API calls were added.

## Boot state machine

| State | Time from start | Presentation |
|---|---:|---|
| Dark | 0–500 ms | Graphite, restrained radial garnet light and a finite scanning line |
| Relic | 500–1,400 ms | Existing `/static/brand/relic-dark.svg`, small opacity/transform reveal |
| Intelligence | 1,400–2,400 ms | Product name, “EVERY REPOSITORY HAS A STORY.” and “REPOSITORY INTELLIGENCE” |
| Reveal | 2,400–3,600 ms | Overlay dissolves; main content receives a 640 ms, 4 px presentation transition |
| Finished | 3,600 ms | Overlay removed, timers cleared and meaningful focus restored |

The ordinary sequence is 3.6 seconds. A separate 4.6-second recovery timer is armed
before phase timers. CSS independently hides the overlay and releases pointer events at
4.8 seconds if JavaScript timers stop. No server-rendered content starts behind a
CSS-hidden application wrapper. If the script never loads, the regular application is
usable immediately. Duplicate initialization or replay while playing does not add an
overlay. Skipping, preference changes, page hiding and navigation cancel owned work.

`archaeologist.intro.v1` is an independent sessionStorage flag; it does not indicate
analysis completion. It suppresses automatic replay across reloads and full-page routes
in the same tab session. If reading/writing session storage is unavailable, automatic
playback is skipped rather than repeated. Manual replay remains usable. This follows
the browser's native tab/session storage lifecycle, including its session-restore rules.

### Replay for a demonstration

Click **Replay Intro** in the workspace context header or public-page footer. **Skip
Intro** is available immediately. Escape dismisses; Tab dismisses and restores focus
instead of trapping navigation behind the overlay. Normal completion focuses `main`
on first entry; replay returns focus to its invoking button. No inert/hidden attribute
is applied to the application, and repository loading continues during playback.

## Living statistics

`LivingStatistics.set(element, numericValue, options)` uses one cancellable RAF per
active metric, cubic ease-out and a default 760 ms duration, bounded to 500–1,200 ms.
The previous visual value becomes the start of a newer update. A newer target cancels
the previous frame; repeated targets and restored snapshot values display immediately.
There are at most 16 concurrent counters. Detached/replaced nodes are released, and
page hiding, pagehide or a motion preference change settles counters to final values.

The utility accepts finite numeric values, including zero, signed values and decimals
within JavaScript's safe numeric magnitude. Null, undefined, nonnumeric or nonfinite
values display `—`. Precision is explicit and bounded to six places; suffixes preserve
units. Intl.NumberFormat is created once per update, not each frame. Numeric source
data and exports are never mutated.

Overview animates existing included-file/source-line/language/directory counts, existing
line totals and skipped-file counts, language percentages with their supplied precision,
and existing structure/relationship/component/C-function score inventories. It adds no
analytical metric. The C-function inventory counts successful model analyses; Python
remains structurally analyzed and unscored by the C model.

An optional bounded session cache stores at most 128 numeric targets, scoped by snapshot
and metric, expiring after two hours. No paths, source text, credentials or model scores
are stored in this presentation cache. Returning to a viewed snapshot avoids count-up
repetition. Storage failure falls back to per-document state. The older general motion
utility remains available to other visualizations; Overview no longer starts its older
integer count-up in parallel.

## Accessibility and performance

- Reduced motion suppresses automatic/manual intro playback and all numeric counting;
  changing the preference mid-operation settles work immediately.
- Counters expose the exact final formatted value in a screen-reader span and mark
  intermediate visual text `aria-hidden`. They create no live-region announcements.
- Skip/replay have native keyboard behavior and visible focus. Intro text is labelled
  as a nonmodal introduction; the application does not become an inaccessible inert tree.
- Opacity and small transforms drive presentation. There are no canvas particles,
  physics restarts, perpetual decorative loops, artificial loading or progress claims.
- Statistic cards retain their dimensions and hierarchy, with tabular numbers, wrapping
  for unusually large values and restrained garnet accent feedback.
- The owned main-content animation is cancelled on dismissal. Listeners and timers are
  removed by controller destruction; pagehide settles presentation without disrupting
  the application's existing BFCache/navigation lifecycle.

## Files

| File | Purpose |
|---|---|
| `app/static/product/cinematic.js` | Boot controller and bounded numeric animation utility |
| `app/static/product/cinematic.css` | Intro, fallback, reduced motion and restrained card treatments |
| `app/templates/cinematic_assets.html` | Shared local asset include |
| `app/templates/public_base.html` | Public-page assets and footer replay control |
| `app/templates/workspace_base.html` | Workspace assets and header replay control |
| `app/static/product/overview.js` | Real summary values and language-percentage animation |
| `app/static/product/workspace.js` | Existing factual pathway counts |
| `tests/frontend/cinematic.test.cjs` | Boot, statistics, accessibility and cleanup contracts |
| `tests/test_cinematic.py` | Harness/route/static integration and pinned-evidence validation |
| `tests/frontend/product.test.cjs` | Browser-like containment/performance and settling presentation before data assertions |
| `tools/task11a_browser.mjs` | Reproducible genuine Chromium acceptance |
| `tools/validate_report.py`, `tests/test_report_pipeline.py` | Explicit frozen-report source verification |

The last pair addresses a release boundary exposed by development: the academic report
manifest intentionally hashes Task 7E frontend sources. Default working-tree validation
still rejects changed sources. The explicit `--source-ref` option verifies every expected
source digest against a full immutable Git commit, still validates actual DOCX/PDF,
figures and metrics, labels that evidence revision and writes no release receipt. The
existing report integration test now uses the exact accepted release SHA; no digest is
silently refreshed and no report/assertion is removed. Additional tests reject changed
hashes and mutable revision names.

## Verification

Fresh baseline: `.venv/bin/python -m pytest -q` → **547 passed**, zero failed/skipped,
14.31 seconds, one existing Starlette/httpx deprecation warning.

Final automated suite: **550 Python tests**, zero failed/skipped in 18.74 seconds,
including the 13-case cinematic harness.
All nine frontend harnesses total **230 cases** (217 existing +13 new). Existing
product assertions inspect settled values; motion itself is tested by the dedicated
timed harness and real browser. No test is skipped or removed. JavaScript syntax checks
cover **30 application files** and **four QA modules**. Local link/figure and approved
vendor checks also pass. Exact test output is recorded in the implementation session;
one pre-existing Starlette/httpx warning remains.

Commands:

```bash
.venv/bin/python -m pytest -q
node --test tests/frontend/cinematic.test.cjs
.venv/bin/python tools/validate_report.py --source-ref 09f6b6df29b6b3e8e81c48c7f8f929a6e638dce5
.venv/bin/python tools/check_report_links.py
.venv/bin/python tools/verify_vendor_assets.py
```

### Real browser acceptance

Sandboxed headless Chromium **157.0.8103.79** used an isolated temporary profile,
native CDP and a separate Uvicorn on port 8013. The user's port 8000 application and
normal browser profiles were untouched. Browser HTTP caching was disabled during QA.

`reports/ui/task11a/browser.json` records 24 positive checks, exact source hashes,
browser version, capture date and fixture. Tests cover all intro exits, once-per-session
navigation/reload, live preference changes, actual ZIP analysis, unchanged C inference,
numeric intermediate/accessibility/final values, cancelled updates, zero/null, cached
snapshot return, blocked storage, CSS fallback, widths 1440/1024/768/390 and counter
completion under 4× CPU throttling. No uncaught JavaScript exceptions occurred.

Actual screenshots, visually inspected:

- `reports/ui/task11a/boot.png` — settled title/relic phase.
- `reports/ui/task11a/overview.png` — genuine university demo analysis and statistics.

Reproduce with a dedicated temporary browser profile (do not reuse a personal profile):

```bash
.venv/bin/python tools/release_smoke.py --write-demo /tmp/task11a-demo.zip
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8013
# In another terminal:
chromium --headless --disable-extensions --remote-debugging-port=9226 \
  --user-data-dir=/tmp/codebase-task11a-chromium --window-size=1440,1000 about:blank
# In another terminal, from the repository:
node tools/task11a_browser.mjs
```

The browser test writes its own QA evidence and briefly creates explicitly scoped utility
probes; those are removed and are not analytical results. The real ZIP uses
`tests/fixtures/university_demo`: two files, 24 source lines, four structural functions
and three genuine C predictions. ZIP ingestion correctly requires no cloud service.

## Limitations and next stage

Physical GPU FPS, screen-reader reading order, touch hardware and full WCAG certification
were not measured. CPU throttling is a browser emulation, not a hardware benchmark.
History/provider network workflows are covered by the unchanged existing suites and
Task 7E evidence; this task did not repeat every live GitHub operation. The branch is
ready for Task 11B after the usual display-specific demo rehearsal. Task 7E report,
screenshots, model and release archive identities remain preserved at the release tag.

Implementation checkpoint: `1db42a0` (`Add optional cinematic boot and living repository
statistics`). The following QA/documentation commit contains this guide, the reproducible
browser script and measured browser evidence. All changes are confined to the cinematic
development branch; its publication is verified against the matching remote branch.
