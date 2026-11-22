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
