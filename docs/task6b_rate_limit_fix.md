# Task 6B.1 — GitHub history reliability repair

## A — diagnosed request flow

Starting commit: f5d89def5992c09a1c6846c18db2a7a1b8865910. Existing tracked tree clean;
three user-owned untracked graph vendor files must remain untouched.

Verified from source, not inferred from a quota message:

- History REST calls are anonymous; environment proxies/redirects are disabled.
- Load performs public metadata + pinned commit list + up to 24 commit-detail requests
  (26 upstream calls). Every tree/compare repeats public metadata and commit discovery.
- Tree retrieval additionally gets Git commit metadata and a recursive tree; comparison
  gets both revision trees and bounded blobs. Reader-local tree/blob caches disappear
  after each API operation. No process cache or single-flight exists.
- Browser retains three trees, but the loaded-tree button explicitly refreshes over HTTP.
  Comparisons retain one displayed result but clicking Compare always fetches again.
- Client request() cancels its previous controller before starting another, including an
  identical pending request. Busy buttons mitigate normal clicks but are not deduplication.
  Cancellation does not guarantee upstream work stops. Rerenders alone do not fetch.
- No automatic frontend/backend retries or panel configuration polling were found.
- Existing ingestion helper recognizes 429 and selected 403 headers as rate limits, groups
  401/ordinary403/404 into inaccessible, and discards quota/reset/request-ID headers.
  Body-indicated secondary limits are not recognized; missing metadata becomes generic UX.

Thus anonymous quota is a constraint, but repeated immutable retrieval, per-operation
cache lifetime and absent coalescing amplify it. This repair will cache validated public,
SHA-scoped evidence, preserve historical identity/coverage, enforce cooldowns, optionally
use a server-only token, and reuse bounded browser results without persisting patches.
No AI configuration, analytical engine, report or visual redesign is in scope.

## Progress

A complete: baseline **475 passed, zero failed/skipped**, one existing Starlette/httpx
deprecation warning (83.86 s). Next: bounded cache and
single-flight tests, accurate upstream status/token handling, client efficiency, final docs.

B implementation: validated method results now share a process-local LRU/TTL cache
(256 entries, 16 MiB total, 2 MiB per entry). Public checks live 60 s, pinned lists 300 s,
commit/tree records 900 s and bounded blob bytes 120 s. Keys include canonical owner/name,
method, exact SHA/arguments, schema and limit configuration; authentication scope follows
in C. Defensive copies prevent per-request mutations from changing cached evidence.
Two bounded per-key producers can run independently; compatible consumers share a flight.
Canceling a consumer does not cancel shared work or close its HTTP client. Failures are
not retained. Each producer owns a client and deadline, including after caller cancellation.
Cache diagnostics expose counts only, no keys. No disk storage or browser patch retention.
Tests: existing 34 history cases and five new cache cases passed individually; the initial
new HTTP mocks incorrectly supplied consumed bodies, corrected to genuine streaming mocks.
B complete: combined focused run **39 passed**, zero failed/skipped. Next C adds token
scope separation, safe quota metadata, cooldown admission and precise errors.

C complete: optional CODEBASE_GITHUB_TOKEN is read/validated server-side and sent only
on fixed api.github.com HTTPS requests. Cache/rate scopes use a process-keyed HMAC, never
the credential itself. Public metadata must report private=false before history is read;
a recent public check is reusable for 60 seconds. Private access is not enabled.
Primary exhaustion, secondary activity limits, unclassified429, ordinary403,401,404,
5xx, redirect, timeout and malformed JSON/content-type are distinguished. Safe quota,
reset, resource, Retry-After and request-ID fields are recorded; malformed values become
unavailable. Shared scope cooldowns block uncached work, not valid cached evidence.
No automatic retries; expiry permits a new attempt but never claims success/reset.
Responses carry safe per-operation X-History-API diagnostics; errors carry optional
error.api metadata. No credential or raw upstream message is reflected.
Tests: **54 passed**, zero failed/skipped, one existing warning. Existing mocked streaming
JSON fixtures now declare the genuine API content type; assertions were preserved.
Next D: browser single-flight, bounded pair reuse, status/cooldown/retry UI and regressions.

D complete: browser requests now coalesce identical in-flight keys, use loaded trees,
and retain at most three / 2 MiB comparison results for 120 seconds in page memory only.
Different revision selection cancels the stale browser consumer; server producers remain
independently bounded. Rerenders and tab switches do not fetch. Comparison/trees and the
larger existing history window survive upstream errors/partial reloads. The subtle API
line distinguishes cached, loading, connected, limited, unavailable and unverified state;
quota values are labeled last reported, local reset time appears only from real metadata.
Explicit Retry respects cooldown without polling or claiming automatic recovery.
Existing five visualization experiences and source-free snapshot lifecycle remain intact.
Tests: **19 product Python checks passed**, including **77 real-document Node cases**
(10 new reliability cases), eight Time Machine view-model and preserved product behavior.
JavaScript syntax checks passed. Browser-rendered acceptance remains unverified here.
Next E: expanded genuine-fixture repeated-operation/cache tests, complete regressions,
security review, documentation and normal push attempt.

## Final request flow and cache contract

The HTTP routes keep their original typed bodies and response objects. Every operation
first passes the cached public-only gate, then reuses validated method results. A pinned
list validates revision membership; it is not rediscovered over HTTP for every panel.
Trees reuse verified commit→tree pointers from the loaded history before requesting
missing tree data. Exact comparison still uses the original bounded tree/line algorithms.
Derived packets are reconstructed from cached facts without changing coverage semantics.

### Evidence storage

| Layer / record | TTL / bound |
| :-- | :-- |
| Process public metadata gate | 60 seconds |
| Pinned commit lists | 300 seconds |
| Parsed commit/tree evidence | 900 seconds |
| Bounded blob bytes | 120 seconds |
| Entire process evidence cache | 256 entries; 16 MiB serialized evidence; 2 MiB/entry |
| In-flight evidence producers | 2 independent keys; same-key consumers coalesce |
| Safe quota/cooldown records | 8 credential scopes; metadata only, no failure bodies |
| Browser comparison cache | 3 results / 2 MiB, 120 seconds; page memory only |
| Browser revision trees | Existing 3 metadata trees / 2 MiB history envelope |

Keys include source schema version, lowercase canonical owner/repository, validated method,
exact SHA(s)/arguments and the full limit configuration. A process-keyed HMAC separates
credential scopes without placing the token in keys. No credential/Authorization header
is stored in cache values, diagnostics, browser state or logs. LRU eviction and monotonic
TTL expiry are predictable; serialized-size bounds do not claim measured Python heap size.
Cache diagnostics are internal aggregate counts, not an endpoint listing keys/data.

Only successful parsed/validated method results are retained. Parsed commit history has
no source patches. Bounded blob content is an explicit short-lived source cache, not a
repository clone. Comparison patches are regenerated from available blobs; they are not
server-cached. Browser patches stay transient: comparison cache and the currently displayed
result are cleared during teardown and never included in snapshot persistence/export.
No disk cache, repository/source archive, credential cache or user snapshot mirror exists.

Single-flight uses a brief thread-safe registry and independent producer tasks, not a global
network lock. Compatible consumers await the same future, receive defensive copies and
cannot mutate stored evidence. A producer owns its own HTTP client and deadline; cancellation
of one browser/operation consumer cannot close another consumer's producer client. Failed
or timed-out producers release their flight slot and do not poison later requests. Admission
limits remain; abandoned producers are still bounded to two flights and their deadlines.

A refreshed public gate is required after 60 seconds even for longer-lived immutable
entries. Visibility may be up to 60 seconds old; if renewal finds private/inaccessible,
subsequent access is denied. This shared cache contains only public upstream evidence,
never uploaded ZIP results or browser-specific conversations. Worker caches are independent,
clear on restart and do not constitute authorization to another user's repository snapshot.

### Optional operator authentication

`CODEBASE_GITHUB_TOKEN` is optional. Configure a fine-grained token with the least public
read access needed, in the server environment before Uvicorn starts. Do not enter it in
chat, HTML, browser storage, URLs, diagnostics or tracked configuration. The existing
`.env` ignore policy is preserved; no .env auto-loader or example secret is added.
The application must still verify `private=false`; authentication does not enable private
repository import/history. This setting applies to Time Machine REST requests, not an AI
provider or a credential-bearing archive redirect. No request goes to another host.

Missing configuration uses anonymous public access. Invalid formatting or upstream401
produces a safe operator-facing authentication error. Changing the token separates cache
and cooldown scope. No successful authenticated live GitHub test is claimed here.

### Quota metadata and failure categories

Safe fields: reported limit, remaining, reset epoch, resource, Retry-After (seconds or HTTP
date), observed timestamp and bounded GitHub request ID. Missing/malformed values become
null. Data comes from responses already needed, never an extra /rate_limit polling request.
`X-History-API` reports cache hit/mixed/upstream/coalesced state, successful cache-hit counts,
coalesced reads and upstream attempts charged to this operation's producer. A shared
consumer may have zero own upstream attempts; it still observes the shared quota ledger.
No scope identifier, cache key, URL credential or configuration value is exposed.

| Condition | API code / interpretation |
| :-- | :-- |
| 403/429, reported remaining=0 or explicit primary message | `github_rate_limit`, `api.kind=primary` |
| 403/429, Retry-After or explicit secondary/abuse message | `github_rate_limit`, `api.kind=secondary` |
| Other429 | `github_rate_limit`, `api.kind=unspecified` |
| Ordinary403 | `github_forbidden`; not quota exhaustion |
| 401 | `github_authentication`; safe server configuration explanation |
| 404 | `github_unavailable`; public repository/revision inaccessible |
| 409 | `github_empty` |
| 5xx / unsupported redirects | `github_upstream`; redirects never followed |
| Network / timeout | `history_network` / `history_timeout` |
| Invalid content type, JSON or parsed evidence | `history_metadata`; not cached |

The longest applicable reported Retry-After and exhausted-primary reset deadline is
respected. Missing usable rate cooldown metadata triggers conservative 60-second backoff,
labeled as such rather than a fabricated reset. A 503 Retry-After is also respected without
calling it rate-limit exhaustion. An already in-flight reply cannot shorten a cooldown.
Successful responses reporting zero remaining also prevent further uncached requests.
Elapsed time only permits another user-initiated attempt; it does not mark GitHub recovered.

No automatic retries occur. During cooldown valid cached method evidence can still serve;
if the public gate expired it must be renewed before server access, so that operation may
remain limited. Browser-loaded history/trees/comparisons remain usable regardless. Different
workloads or applications can consume the same GitHub allowance, so no quota guarantee exists.

## Frontend lifecycle and privacy

Exact pending request keys deduplicate fetches. Different selections abort stale browser
consumers and epoch checks discard late replies; they do not cancel shared server work.
Already loaded trees bypass HTTP. Cached pairs are keyed by directed full base/head SHAs;
reverse comparisons are distinct. Comparison cache resets on repository initialization,
pagehide and expiration of entries, and is byte/count bounded. No panel fetches on rerender.

The status line distinguishes last reported API state from cache use. Reset times are
localized only when provided; backoff is explicitly named and never presented as a known
primary reset. Retry stays keyboard accessible and is manual. Client cooldown admission
blocks new work, while cached evidence remains accessible. Failures preserve the active
view and previous successful pair; a smaller partial history response cannot discard a
larger retained pinned window. Loading/cancel controls remain truthful.

## Verification and local acceptance

Deterministic tests use mocked streaming GitHub responses and genuine Git fixture objects.
Repeated seven-commit load uses **9 calls initially, 0 on reuse**. A divergent exact
comparison after that load needs **4 additional calls** (two missing trees, two blobs);
its repeat and both already loaded tree requests use **0 additional calls** while caches
and the public gate remain valid. These are measured mock transport request counts, not
live-network latency or FPS claims. Final suite results are recorded below after completion.

Coverage includes cache hit/miss/TTL/LRU/bytes, repository/SHA/parameter/auth isolation,
concurrent identical/independent work, cancellation/deadline/failure recovery, token secrecy,
primary/secondary/ordinary403/401/404/429/5xx handling, malformed/reset/HTTP-date metadata,
content type/JSON, exact revisions, public-only access, bounded transport, shared admission,
client cached pairs/trees, rapid switching, retries, stale responses and preserved views.
Existing tests/coverage are preserved; old JSON mocks were corrected to declare content
type and expose actual streams because error bodies are now inspected safely.

```bash
source .venv/bin/activate
python -m pytest -q tests/test_history_cache.py tests/test_history.py tests/test_product.py
python -m pytest -q
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

The product Python runner invokes Node tests over actual generated route documents and
genuine history fixture responses. On a normal browser, import a small public GitHub repo,
load Time Machine once, compare two revisions repeatedly, view each tree repeatedly and
switch all five visualizations. Use Network to confirm client cache hits issue no request;
for server hits inspect safe X-History-API metadata. Test with/without an operator token,
permission failures, offline mode and actual rate responses if encountered naturally.
Do not deliberately exhaust GitHub quota. Verify local reset/cooldown wording, manual retry,
keyboard access, preserved selection, cached playback, refresh and repository replacement.

Sandbox attempts for this repair: GitHub DNS failed (curl6 for api.github.com); Chromium
exited133 before rendering with setsockopt Operation not permitted; Uvicorn reached startup
but could not bind localhost. No live GitHub/authentication, screenshots, rendered responsive
acceptance or FPS improvement is claimed. The full history source/coverage, 24-commit window,
source bounds and Task5/6B design remain. No AI provider, ML model, dataset or report changed.

## Reference contracts

Behavior checked against official GitHub [REST rate limits](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api)
and [REST best practices](https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api).
Authentication can raise primary allowance according to GitHub policy; secondary limits
still apply. Fixed-host/no-redirect handling intentionally preserves this application's
stricter ingestion security boundary. No success time is promised.

## E complete — final verified results

- Baseline: 475 Python tests passed. Final complete suite: **502 passed, 0 failed,
  0 skipped**, in 86.37 seconds; one pre-existing Starlette/httpx deprecation warning.
- New backend reliability suite: **27 cases**. Frontend: **77 actual-document cases**,
  eight Time Machine view-model cases and 16 storage cases, alongside preserved graph24,
  architecture10, impact32 and Jordan30 suites. Node cases are invoked by Python runners
  and are not added to the Python test total.
- Genuine Git fixture request-count checks verified nine initial load calls, four more
  for a divergent exact comparison using cached commit→tree pointers, zero on repeats.
  Cancellation/deadlines, unknown metadata, credentials, scopes and partial results passed.
- Source/engineering review preserved all five views, exact SHA direction, null/zero
  distinctions, snapshots, cached playback, safe text rendering and prior successful views.
  Only the subtle status/retry presentation changes; no visual redesign or new dependency.
- Browser startup failed before rendering (Chromium133); application startup succeeded
  but localhost bind failed (Uvicorn3); GitHub DNS failed (curl6). Live API/token and rendered
  visual acceptance remain local manual checks, not claimed successes.

A–E are preserved in five descriptive incremental commits including this final stage.
User-owned untracked vendor assets remain untouched. No ML/report/provider work was done.
Normal push is attempted after this commit; if DNS still fails, retry `git push origin main`
from the project directory when connectivity is restored. Never force-push.
Final static checks also passed: JavaScript syntax, Python3.10 grammar, pip dependency
consistency, documentation links, CSS block balance, diff whitespace, intended file paths,
file sizes and credential-pattern review. No vendor asset, dataset, artifact, secret or
academic report is included in these changes.
