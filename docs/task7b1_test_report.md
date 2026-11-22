# Task7B.1 — regression and acceptance report

## Overall status

**PARTIALLY COMPLETED**: actual frontend motion is implemented; automated checks pass
as recorded below. New browser-only visual/touch/responsive/performance acceptance is
unverified. The user reports7B works locally; this does not certify new7B.1 animations.
No demonstrated critical regression is known in exercised analysis/UI contracts.

## Test executions

Baseline full suite: **508passed,0failed,0skipped in94.24s**, one existing Starlette/httpx
deprecation warning. Final full suite after the second quality pass: **511passed,0failed,0skipped
in102.32s**, same one warning. The prior full run also passed511/102.09s.
Exact normal command: `.venv/bin/python -m pytest -q`. This socket-restricted environment
uses the process-local selector wrapper printed in task7b1_baseline.md; application
networking is not patched. Existing tiny reproducibility-test fits are unchanged; no
benchmark model was retrained or reevaluated to improve results.

Focused runs: primitive Python2passes/1.12s; shell/product21passes/41.33s;
visualization/product27passes/44.91s; Jordan/history/product22passes/41.65s;
updated actual-document/motion22passes/42.99s. No failed/skipped tests in these runs.
All29non-vendor applicationJSfiles pass `node --check`; pip check and diff check pass.

Explicit frontend execution on genuine existing generated source/Git fixtures:

| Harness | Cases passed | Failed/skipped |
|---|---:|---:|
| motion.test.cjs |14|0/0|
| graph.test.cjs |26|0/0|
| architecture.test.cjs |10|0/0|
| impact.test.cjs |32|0/0|
| jordan.test.cjs |30|0/0|
| workspace.test.cjs |16|0/0|
| product.test.cjs |80|0/0|
| time_machine.test.cjs |8|0/0|

These216Node cases include cases invoked inside Python wrappers. **Do not add them to
the Python test total.** Product/time_machine use PRODUCT_FIXTURE supplied by the actual
FastAPI/Git test harness, not live GitHub or fictional commit data.

## New regression coverage

`tests/test_motion.py`: new local asset/safe-content contract, script loading order and
preserved branding routes, and Node motion lifecycle runner.14Node primitive cases
exercise native-effect completion/cancellation, repeated begin/destroy, exact accessible
final metric values/formatting, reduced preference at start and live, hidden-document
cleanup, detached/replaced DOM, bounds, one-shot observation, per-snapshot/tab seen scope,
blocked storage/API fallback, focused content, busy flags, dimmed path emphasis and
narrow viewport motion settings. The graph harness adds a current-preference duration
case while retaining7B pan/fit/reset/resize/cleanup checks. Three product cases verify
BFCache lifecycle/no reanalysis, latest-message-only entrance/local failure cleanup,
and pending-history cancellation with loaded evidence preserved.

## Acceptance matrix

| Area | Status | Actual evidence / limit |
|---|---|---|
| Core source analysis / genuine C inference / archive security |PASS automated|Full existing tests preserved; no analytical/runtime backend modules changed. |
| Navigation, snapshots, history caching and cancellation |PASS automated|Existing product/store/history regressions and new lifecycle/busy assertions. |
| Motion utility and safe fallback |PASS automated|14deterministic unit cases plus actual-document integration. |
| Final metric values / accessibility structure |PASS automated|Only four integer overview metrics; final sr-only values, aria-hidden intermediate span, finish/cancel settles text. |
| Reduced motion / hidden tab |PASS automated; PARTIAL browser|JS and CSS suppression, live media/hide cleanup, dynamic camera duration and static statuses verified in harness. Actual rendered assistive behavior pending. |
| Node/edge/data accuracy |PASS automated|No layouts, metrics, history or evidence algorithms replaced; actual dim opacity/dash final style preserved. |
| Brand preservation |PASS automated|No brand asset changes; existing asset/route tests retained. |
| Layout / actual cinematic appearance |NOT VERIFIED|Chromium cannot render here; source review is not visual acceptance. |
| Responsiveness at target sizes / touch |PARTIAL|Narrow motion settings tested;1440/1024/768/390/320 rendered geometry and touch need local browser. |
| Physical3D camera and GPU performance |NOT VERIFIED|Controls/configuration/harness pass; no real GPU observation or FPS measurement. |
| Cloud mode |NOT VERIFIED live / unchanged scope|No credentials configured or provider called; existing mocked consent/error tests preserved. |

## Browser / performance observations and remaining limitations

Fresh attempt: Chromium headless with temporary profile, no-sandbox/dev-shm flags and
core dumps disabled exits133 at `setsockopt: Operation not permitted` before rendering
about:blank. Uvicorn startup succeeds then cannot bind127.0.0.1:8000 (exit3). No website
screenshots, recorded animation timing, FPS or visual signoff are claimed.

Engineering bounds, not measured speed claims:24native effects,12items per group/trace,
4finite counters, capped delays, seen80keys with snapshot expiry/2hour TTL. There is no
new physics simulation, hidden-page active counter, per-cell timer, background polling,
provider request, source execution or unbounded cache. Busy CSS repeats only during real
pending operation and pauses when hidden. Counters/observers/effects/media listeners
clean up on lifecycle end; detached targets are pruned. Colors/layouts are not animated
into fabricated data. Cached evolution does not replay a reveal on every revision frame.

Native details close/dropdowns/SVG title tooltips retain browser behavior; no custom
closing animation framework added. Seen-key eviction or unavailable storage can permit
later repeat visual reveals. Ongoing camera transition cancellation at an OS preference
change is not claimed; subsequent camera actions immediately use0ms reduced duration.
No claim of a newly fixed cross-browser rendering defect can be made without a browser.
Use the mandatory local checklist before new visual acceptance/report screenshot claims.

## Final quality review / delivery

Reviewed original-to-final diff and confirmed no changes to backend routes/analysis/
ML/ingestion/history/provider modules, branding assets, README or report binaries.
The second source review applies nonzero entrance frames during bounded stagger delays
with backwards fill and no forwards retention; the final full suite above covers that
policy. No original tests were removed, skipped or weakened. Three new Python checks,
14motion cases, one graph-preference case and three product lifecycle/request cases
provide focused coverage. These are deterministic harnesses, not actual native browser
animation observation. All29syntax checks and document links pass after final changes.

Six required7B.1 documents are present. Checkpoint commits:8efafee,0b2d133,c85d95b,
9c9b866,16393bf; final quality/test documentation commit follows these results.
Three original vendor assets remain unchanged and untracked; no secrets staged.
Normal push outcome is reported in the completion response; if networking remains
unavailable, retain commits and run `git push origin main` locally.
