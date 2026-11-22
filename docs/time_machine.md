# Codebase Time Machine

## Purpose and sources

`/workspace/time-machine` investigates authentic commits, changed paths and exact revision
trees. It adds history retrieval to an existing analysis; opening or changing its views
does not repeat ZIP extraction, parsing, ML inference or repository analysis.

Public GitHub imports provide the validated canonical URL and full pinned snapshot SHA.
**Retrieve Git history** explicitly fetches a bounded window anchored at that SHA through
the GitHub REST API. An ordinary ZIP contains no usable history in this application:
it receives a no-history explanation and a link to import a public GitHub repository.
Archive timestamps are never interpreted as commits. Private repositories, arbitrary
branches, browser-supplied local directories and abbreviated revision IDs are unsupported.

An operator/test-only `LocalReader` can inspect a trusted local Git directory. No HTTP
route accepts a filesystem path. Git is needed for the genuine-history test fixtures,
not public REST history retrieval. No clone, checkout, hooks, filters, submodules or builds
are run by the public history service.

## Architecture and contracts

- `app/history/models.py`: typed commit, change, tree, comparison, coverage and limit models.
- `app/history/core.py`: validation, UTC activity, path churn, exact tree differences,
  bounded text differences and serialized-history limits.
- `app/history/github.py`: fixed-host public REST retrieval, scoped evidence reuse and deadlines.
- `app/history/cache.py` / `status.py`: bounded validated evidence cache, single-flight and quota/cooldown accounting.
- `app/history/local.py`: read-only bounded Git fixture/operator adapter.
- `app/routes/history.py`: typed operations; no server user-snapshot/session store. Public upstream evidence has a bounded process cache.
- `app/static/time_machine/`: shared pure view models, workspace lifecycle, timeline,
  spatial landscape, comparison studio and revision evolution modules.

All requests are JSON POSTs. Unknown fields are rejected. SHA fields require full lowercase
40-character Git object IDs. URL validation reuses the secure GitHub ingestion parser.

| Endpoint | Request | Response |
| :-- | :-- | :-- |
| `/api/history/load` | `url`, `anchor` | `History`: schema `1.0`, canonical URL, anchor, commits, activity, churn, coverage, limits, source |
| `/api/history/tree` | `url`, `anchor`, `revision` | `RevisionTree`: revision, sorted file metadata, completeness, issues |
| `/api/history/compare` | `url`, `anchor`, `base`, `head` | `Comparison`: exact direction, changed files, available text statistics/patches, completeness, issues |

Tree and comparison revisions must belong to the retained anchored commit window, verified
again server-side. A public repository URL is not an authorization token: these endpoints
only retrieve public upstream evidence and hold no other user's repository context.
Existing analysis endpoints and their response fields remain unchanged. Browser export
adds optional `history` after retrieval, including bounded cached tree metadata. Transient
comparison patches are not attached to the analysis, persisted or exported.

A commit contains SHA, actual parent SHAs, tree SHA, author display name, timezone-aware
author/committer dates, bounded subject and changed files. Email addresses are not extracted.
A changed file contains path, status, optional prior path, nullable additions/deletions and
measurement status. Missing measurements remain null. Tree records contain actual path,
object SHA, mode and optional byte size; symlinks/gitlinks remain metadata only.

## Retrieval and security

Requests are constructed from validated owner/repository identifiers at fixed
`https://api.github.com/repos/...` endpoints. URLs returned in responses are not fetched.
Redirects and environment proxies are disabled; there are no user download hosts or
automatic retries. Optional `CODEBASE_GITHUB_TOKEN` is read only on the server and sent
only to the fixed GitHub API host. A public-only metadata gate (60-second cache) precedes
history access, even when configured credentials could access private repositories. Streaming response caps apply even without Content-Length. Blob content
is bounded and its Git blob SHA is verified before comparison. Validated public evidence is cached with explicit TTL/byte/entry limits; bounded blob
bytes expire after 120 seconds. No repository is downloaded to persistent server storage.

Upstream authentication/inaccessibility, rate limits, timeouts, network errors and malformed
metadata produce safe application errors. If a resource/rate limit occurs after some commit
details were retained, collection can return explicitly partial evidence. A failure before
usable details produces an error, not fabricated fallback history. Exactly one full page
of changed files is conservatively marked incomplete. Incomplete revision trees cannot
establish file absence, so exact comparison is refused rather than inventing deletions.

The trusted local adapter uses argument arrays, strict revisions and a small environment,
with system/global Git config, hooks, fsmonitor, attributes, optional locks, replacements
and prompting disabled. Output and runtime are bounded. It never checks out content,
follows symlink targets, recurses into submodules or exposes its local path in results.
Tests create repositories themselves; their setup commands are not exposed through APIs.

Untrusted names/messages are rendered with DOM text nodes, patches in literal `pre`
elements. Controls/bidi markers in display metadata are escaped and clipped text ends in
an ellipsis. Unsupported relative paths are rejected. Source patches never execute and
are not sent to an AI provider. Jordan/provider code and consent behavior are unchanged.

## Default limits

Analysis defaults live in `HistoryLimits`; cache bounds live in `EvidenceCache`. The
only new optional environment setting is the server-side GitHub token.

| Resource | Bound |
| :-- | --: |
| Retained commits | 24 (request one extra to detect a larger window) |
| Changed files per commit | 100, first REST page only |
| Total file-change safety cap | 4,000 (24 × 100 is the normal effective bound) |
| Retained tree entries | 5,000 |
| Comparison changed files | 200 |
| Text comparison candidates | First 8 sorted changed-file records |
| Individual regular-file text | 64 KiB / 2,000 lines |
| Patch output | 64 KiB total; at most 16 KiB per file |
| Individual upstream JSON / retained history | 2 MiB |
| Total upstream transfer per operation | 12 MiB |
| Upstream requests per operation | 90 |
| Operation deadline | 60 seconds |
| Connect / read timeout | 5 / 10 seconds |
| Incoming request body / body-read deadline | 4 KiB / 10 seconds |
| Concurrent repository operations | 2, shared with ingestion |

The client aborts at 65 seconds and provides Cancel. These are conservative safety defaults,
not measured optimal settings or full-history guarantees. A normal 24-commit load needs
approximately 26 upstream requests; subsequent comparisons/trees reuse validated lists, commit/tree metadata and blobs.
Cache misses and genuinely new revisions still consume quota. No silent retry storm
is introduced. Optional authentication can raise the allowance according to GitHub policy. Large upstream JSON may fail before post-parsing bounds.

## Ordering, ancestry and dates

REST list order is preserved as returned for the pinned SHA; it is not advertised as
complete topological order. The trusted local adapter uses Git topological order. Coverage
records scope, ordering, missing parents and limits. Complete ancestry means the retained
parent closure is complete, not that every branch/tag in the repository was inspected.
Shallow local history remains marked shallow even when boundary metadata looks root-like.
Missing merge parents are explicit. Branch names are not invented from parent structure.

The timeline separately sorts by **committer timestamp**, then SHA. It is **event-spaced**:
spacing expresses ordered commits, not elapsed duration. Curves connect only actual retained
parent/child relationships; multiple actual parents produce merge markers. Committer dates
can disagree with ancestry, so the inspector retains parent evidence and both date fields.
Original date offsets are preserved; activity and filter date boundaries use UTC committer
dates. Activity counts commits, not contributions, productivity or software quality.

## Metrics and rename semantics

- **Touches:** distinct retained commits with a change record for a particular path.
- **Added/deleted lines:** sums of available text measurements; aggregate becomes unavailable
  if any contributing record is unmeasured. Known measured subtotals remain separate.
- **Changed lines:** additions plus deletions, only when both are measured.
- **Directory aggregation:** sums file metrics below the real directory. A touch sum counts
  file-change events, not unique commits to the entire directory.
- **Activity:** commits aggregated into UTC days/months. The landscape shows up to 24 calendar
  months ending at the latest observed month, including empty months within that window.
  Zero means no retained commits on that date, not proof of repository-wide inactivity.
- **Churn history:** path-scoped, with actual reported previous-path evidence. It does not
  claim complete identity continuity across every rename or copy.

REST change status/statistics are upstream facts. Missing patches are treated conservatively
as unmeasured text, including binary/large-file cases. Comparison uses exact base and head
Git trees, not a merge-base comparison. Rename detection pairs a removed/added path only
when blob SHA and mode are identical and the pair is unique. Ambiguous identical copies
remain additions/removals. Similarity-based edited renames are not claimed.

Bounded UTF-8 regular files use Python `SequenceMatcher` line differences and unified
patches. Counts are exact for that documented algorithm and available input, not guaranteed
to match every Git diff heuristic. Binary, non-UTF-8, special, oversized and out-of-budget
entries have explicit unavailable statuses. Patch clipping does not turn unknown totals
into zero. Per-revision complexity and ML inference are not performed.

## Visualizations and interactions

### Commit timeline and activity

A directional SVG timeline supports pointer panning, focal-point wheel zoom, zoom buttons,
Fit History, keyboard selection and persistent selected commit. Dates and labels are
contextual; node/text sizes stay in screen units during zoom. The inspector provides full
SHA, dates, parents, measured changes, merge evidence and coverage. Selecting a commit can
open its exact tree or set a comparison base. Monthly activity bars use actual UTC counts;
selecting a month narrows the date range. Search/date filters affect timeline/activity/churn,
not the explicit revision pair or exact tree selectors.

### Churn landscape

A deterministic balanced spatial partition groups actual directory paths. Area uses the
selected metric (touches, additions, deletions or changed lines), with a one-unit visibility
floor for zero/unavailable entries. Color reflects measured magnitude, neutral zero and
hatched unavailable data. Nested directory previews are bounded; drill-down, breadcrumbs,
full-path search, click/keyboard inspection and paginated overflow preserve access. A
large region indicates a historical measure, never a defect probability.

### Revision comparison studio

Base/head selectors contain real retained revisions. Compare is explicit; selection alone
does not fetch. Results label added, removed, modified and exact-blob renamed paths, separate
measured totals from unmeasured files and offer literal bounded patch evidence. Reversing
the pair reverses the comparison direction. Comparison results remain in page memory only; source blobs may also occupy the bounded
120-second server evidence cache. Patches themselves are not server-cached or persisted.

### Evolution explorer

Fetch the exact tracked tree for a selected retained commit, scrub actual revisions and
inspect directory/file regions by tracked entries, available bytes or reported changed
entries at that commit. Changed-entry values can be unavailable when commit details were
partial. A removed path is absent from the later tree. No interpolated trees, per-revision
risk scores or filesystem timestamps are presented as historical evidence.

Optional playback visits **already loaded actual trees only**, ordered by committer date,
with a 1.4-second step. It does not fetch during playback. Pause, scrubbing, hidden pages,
view changes and teardown stop it; reduced-motion users cannot start it. Up to three
metadata trees can be cached, further pruned to the shared history byte budget.

## Lifecycle, navigation and performance

History belongs to the same analysis object in IndexedDB, with the existing per-tab active
pointer. Saving it preserves snapshot ID, creation date and two-hour expiry. It never
refreshes retention or creates another analysis. Shared bounds remain three snapshots /
24 MiB per row, with a stricter 2 MiB history envelope. Normal reload restores history and
bounded trees; transient source diffs do not survive. Repository replacement/expiry drops
context; epoch checks and request cancellation reject late responses. No server mirror of browser snapshots or conversations is added. The shared server cache
contains only recently verified public GitHub evidence under separate credential scopes,
not uploaded ZIP data, per-user history state or credentials. Browser storage is not encrypted.

Current structure, graph and heatmap file inspectors can launch file history using stable
file IDs. Historical/current links require matching canonical repository URL, pinned SHA
and an unambiguous inventory path (including a single common ZIP wrapper where justified).
Deleted/renamed historical paths are not silently linked to unrelated current files. Current
structure/graph links explicitly describe current snapshot context: its ML scores and
complexity were not measured at the historical revision.

Modules load only on the dedicated page. SVG objects are reused during selection/viewport
updates; bounded labels and top-level regions avoid thousands of DOM nodes. Inactive view
renderers are destroyed, search is debounced, playback is event-controlled and request/
pagehide listeners are cleaned up. No WebGL, physics simulation, heavy visualization
library, perpetual animation, MSAA or high-DPI canvas is introduced. CSS adapts controls
and the native collapsible inspector for narrow widths; actual rendered responsiveness
still requires local browser acceptance. No FPS improvement is claimed.

## API reliability repair — Task 6B.1

Validated public metadata, pinned commit lists, commit details, revision trees and bounded
blobs now share a process-local LRU cache: **256 entries / 16 MiB serialized evidence /
2 MiB per entry**. TTLs are 60 / 300 / 900 / 900 / 120 seconds respectively. Credential
scope, canonical repository, method, exact revision/parameters, schema and limit values
form the internal key. Two per-key producers can run independently; identical consumers
share one bounded producer. Canceling one consumer does not corrupt shared work. Cache
miss failures are not stored. Tree lookup reuses a cached verified commit's tree SHA.

The browser reuses loaded metadata trees and up to three / 2 MiB cached comparison results
for 120 seconds, in page memory only. The current displayed comparison may remain visible
until navigation; its source is never persisted/exported. A retryable failure preserves
successful views. Smaller partial reloads cannot replace a larger pinned history window.
A subtle live status line displays cache/loading/connection state, **last reported** quota,
reliable reset timestamps in local time and explicit cooldowns. Retry is user initiated;
there is no polling, automatic retry or assertion that elapsed reset time guarantees success.

Successful API responses include optional `X-History-API` JSON diagnostics. Failures may
include `error.api`; codes distinguish authentication, permission, inaccessible repository,
rate limiting and upstream/network/metadata failures. Rate failures further identify
primary, secondary or unclassified restrictions. Cooldowns apply to uncached upstream
work; already loaded browser evidence remains available. A fresh public gate is needed
once its short TTL expires, even if some immutable server entries remain cached.

Optional Bash configuration before starting Uvicorn (do not paste keys into chat/UI):

```bash
read -rsp 'GitHub public-read token (optional): ' CODEBASE_GITHUB_TOKEN
export CODEBASE_GITHUB_TOKEN
```

Use a fine-grained token restricted to the public read access needed for the selected
repositories. No private-repository support is introduced. No token field, credential
endpoint, key log or token persistence exists. This setting applies to history REST
operations; ZIP ingestion and existing snapshot import contracts are unchanged.
Anonymous mode remains supported. No AI provider configuration is involved.

Process-local caches are not shared across Uvicorn workers and disappear on restart.
Visibility checks can be up to 60 seconds old; previously public immutable data expires
according to its bounded evidence TTL. New/uncached access is denied if the renewed
metadata check reports private/inaccessible. Tokens changing scope cannot reuse one
another's entries. Quotas shared with other programs/IPs can still be exhausted; large
responses may exceed source limits. This repair reduces avoidable calls, not GitHub's
policy limits. No latency or FPS improvement is claimed.

[Diagnosis, exact cache/cooldown behavior and repair verification](task6b_rate_limit_fix.md).

## Verification and limitations

Tests create genuine Git repositories with controlled commits, authors/timezones, branch
and merge ancestry, identical-blob rename, deletion, binary/special entries, unusual names,
shallow clones and detached HEAD. Mocked REST responses are derived from those actual Git
objects. Tests cover exact divergent comparisons, ambiguity, unavailable statistics, bounded
patches/trees/transport, rate limits, safe metadata, shared admission, object isolation,
source-free persistence, cancellation, stale responses and real FastAPI documents.

Browser-free JavaScript tests exercise actual route HTML with genuine fixture responses,
plus deterministic spatial/date/identity utilities and snapshot lifecycle checks. They are
not browser/GPU, accessibility-audit or visual acceptance results. The final verified counts
are recorded in [the implementation log](task6b_progress.md).

This sandbox blocked Chromium before rendering (`setsockopt: Operation not permitted`,
exit 133), Uvicorn localhost binding after successful startup, and GitHub DNS resolution.
No live GitHub history, screenshots, rendered responsive acceptance or measured FPS is
claimed. Jordan historical question support remains future integration; current local
intelligence and provider behavior are preserved.

### Run and accept locally

```bash
source .venv/bin/activate
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
python -m pytest -q tests/test_history.py tests/test_product.py
python -m pytest -q
node tests/frontend/workspace.test.cjs
```

`test_product.py` invokes the real-document Node suite and Time Machine utility tests using
a generated genuine-Git fixture; they need Node and Git but no network. Socket-restricted
test environments can use the selector wrapper documented in `ml_pipeline.md`.

1. At 1366×768, import a small public GitHub repository through `/explore`, then open Time
   Machine and explicitly retrieve history. Check canonical URL/anchor against overview.
2. Inspect parent links, full dates, merge markers and several changes against GitHub/Git.
   Pan/zoom around a selected commit, fit, use keyboard selection and month/date filters.
3. Switch all churn metrics, drill directories, inspect missing/zero values and rename
   evidence. Search a deleted file; verify it is not linked to an unrelated current file.
4. Compare two retained revisions in both directions. Verify statuses and available patches;
   do not compare patch counts against a different merge-base or Git algorithm silently.
5. Load several exact trees, scrub, play cached revisions, pause and hide/switch pages. Test
   reduced motion. Check entry modes, byte labels and absence of deleted paths.
6. Refresh/back/forward; visit graph, structure, Jordan and heatmaps without reanalysis.
   Launch file history and confirm exact identity. Replace/forget the repository during an
   outstanding request; stale history must not attach. Export metadata, not source patches.
7. Upload a normal ZIP: no history request/charts should appear. Exercise network failure,
   rate limiting, cancel and partial history. Repeat at 390px/tablet widths, long paths,
   keyboard focus, expanded inspector and browser console. Capture only authentic screenshots.
8. Use Chrome Performance/Memory recordings for repeated selection, view changes and
   teardown on integrated graphics. Measure before making latency/FPS/leak claims.

## Endpoint references

Contracts checked against the official [GitHub commits REST documentation](https://docs.github.com/en/rest/commits/commits),
[Git trees](https://docs.github.com/en/rest/git/trees) and
[Git blobs](https://docs.github.com/en/rest/git/blobs). Public retrieval uses list/get commits,
Git commits, recursive trees and blob-by-SHA endpoints. GitHub's merge-base comparison API
is deliberately not used for the exact snapshot comparison promised here.
