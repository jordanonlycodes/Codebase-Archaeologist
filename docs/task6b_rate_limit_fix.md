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
