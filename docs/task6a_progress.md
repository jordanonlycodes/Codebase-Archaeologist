# Task 6A — Jordan progress

## Stage A complete — audited architecture

Baseline: 402 Python tests passed, zero failed/skipped (one existing Starlette/httpx
warning). Existing Node regression runners are included in that suite. Used the
process-local polling selector workaround documented in ml_pipeline.md.

Decisions:
- Local retrieval and deterministic answers run in the browser over the active,
  source-free IndexedDB snapshot. Index once per workspace lifecycle; reuse the
  existing bounded Blast Radius engine. No new parsing or server repository cache.
- Optional OpenAI Responses adapter receives only a typed, bounded evidence package
  after explicit per-request disclosure consent. Server assigns citation IDs and
  rejects unknown citations. Client-supplied facts cannot be independently verified
  against a server snapshot; this trust boundary will be explicit.
- No full source explanation: function bodies are removed after ingestion. Local
  summaries describe metrics and observed relationships, not implementation behavior.
- Conversation remains per-tab, snapshot-scoped, bounded, and expires with its
  snapshot. Cloud answers are not persisted. Provider credentials stay server-side.
- Preserve untracked vendor assets, analytical engines, model artifacts and reports.

Next: B evidence indexing/tests; C local intents/tests; D provider/consent API;
E dedicated workspace; F stable-ID handoffs; G full regressions, docs and review.

## Stage B complete — evidence retrieval

Added a snapshot-local lexical index over real graph entities, components and retained
structural functions. Exact/partial matching preserves same-name ambiguity. Evidence
records retain IDs, paths, lines and categorical facts; packets cap at 12 records and
24 KiB. Conversation helpers filter by snapshot and local mode, at most eight turns
and 18 KiB. Six deterministic Node cases passed (retrieval, provenance, ambiguity,
unknown context, bounds, isolation and untrusted text). No network or source retention.

## Stage C complete — local intelligence

Added supported intent interpretation and evidence-backed deterministic answers for
summaries/languages/counts, complexity/hotspots, scored/unscored functions, coverage,
entity lookup, callers/callees, imports/includes, components, two-file relationships
and bounded impact paths. Pronouns use a validated selected entity; ambiguity produces
candidates. Unsupported requests explain capability boundaries. Existing impact engine
provides direct/transitive direction and actual edge evidence, with its original limits.
23 Node cases passed, including cycles, ambiguity, file/component membership, imports,
missing model scores, partial/empty data, output bounds and reproducibility.

## Stage D complete — optional provider boundary

Added typed capabilities/explanation APIs and a replaceable provider protocol with one
implemented adapter: fixed-host OpenAI Responses API, verified against official create
and structured-output documentation. Explicit enable/key/model configuration, per-request
consent, same-origin browser checks, pre-parser 32 KiB transport cap, 24 KiB evidence,
two concurrent cloud requests/process, upload/connection/read/total timeouts, bounded
response, no redirects/retries/tools, store:false, strict output and citation validation.
Provider exceptions are scrubbed; keys are excluded from repr/responses. No server
snapshot or conversation cache. 29 focused Python checks passed (including the 23-case
Node runner); all provider traffic mocked. No live cloud test or credentials used.

## Stage E complete — dedicated Jordan workspace

Added /workspace/jordan with lazy assets, existing typography/tokens, responsive
collapsible repository/evidence regions, safe text-only conversation, real citations,
local follow-ups, bounded snapshot-scoped history, new investigation and cancellation.
AI enhancement prepares an exact disclosure preview; a fresh explicit checkbox and send
are required for each request. Withdraw/mode-change/pagehide abort client requests and
clear pending disclosure. Local answer remains available on provider failure. Cloud
answers are memory-only. Existing shared lifecycle restores local conversation and
cleans up requests on navigation; no source payload or second repository cache.
The initial focused run passed 18 Python checks and exposed one case-sensitive
preview assertion error. After correcting it, the real-document harness passed all
38 cases directly. The final full Python run will verify the complete runner again.
This is browser-free integration, not visual verification. No landing styles changed.

## Stage F complete — contextual investigations

Added exact-ID Ask Jordan handoffs from structure, risk, graph, architecture/heatmaps
and impact inspectors, plus Overview entry. Handoffs contain only validated identities,
origin page, a bounded suggested question and optional impact depth/direction/target.
The selected path is retrieved again from the existing engine, not trusted as supplied
source evidence. Jordan can return to the originating page and navigate evidence to
structure, graph, architecture and impact without reanalysis. Architecture summaries
include actual directory grouping and recorded dependency cycles.
Verified: 41 real-document cases, 24 graph, 10 architecture, 32 impact Node cases passed.
No source parser, trained model, academic artifact or landing design was modified.

## Stage G complete — final review, documentation and verification

- Final full suite: **435 Python tests passed, 0 failed, 0 skipped**, one pre-existing
  Starlette/httpx deprecation warning. New provider/retrieval runners and Jordan route
  are included. No existing tests removed or weakened.
- Current direct Node checks: **30 Jordan**, **44 real-document journeys**, **15 store**,
  **24 graph**, **10 architecture**, **32 impact** cases passed. The last focused Jordan
  checks cover relationship-type filtering, same-path component ambiguity, full identity
  versus abbreviated disclosure, recursion and within-file relationship evidence.
- Real in-process ASGI mixed ZIP smoke: 3 files, 2 directories, 5 physical lines,
  4 structural functions, model ready with 2 genuine C predictions, graph 10 nodes /
  12 edges. Verified load_settings → parse_config and its reversed potential-impact
  path with real source references. No training/held-out evaluation was run.
- JavaScript syntax, Python compilation, local documentation links, CSS block balance
  and git diff whitespace checks passed. Reviewed intended files/ignore rules; no
  secrets, raw datasets, source archives, artifacts or report updates staged.
- Python 3.10 compatibility review replaced newer asyncio timeout context APIs with
  wait_for; deterministic tests cover provider total deadline/request-read timeout.
- Privacy review: explicit fresh consent per cloud send/retry; withdrawal/cancellation
  and navigation invalidate late responses. AI replies never enter persisted history.
  Missing/expired pointers also clear leftover conversation preferences. Plain text
  rendering prevents HTML/Markdown execution. Server/client factual trust boundary is
  documented; valid citations are not an entailment guarantee.
- Design/source review: scoped native fonts/tokens, restrained editorial Jordan identity,
  compact toolbar, composer, evidence citations, full-path inspector, collapsible panels,
  reduced motion and preserved original landing. Narrow panels do not open themselves
  merely because an answer arrives. No continuous animation or new rendering dependency.
- Browser attempts: Chromium exit 133, `setsockopt: Operation not permitted`; Firefox
  exit 139 before rendering. Uvicorn imported and reached startup, then exit 3 because
  localhost:8000 could not bind. No website visual, responsive, GPU, screenshot or FPS
  verification is claimed. In-process route and real-document checks succeeded.
- No live cloud call: credentials were not supplied or used; all provider tests mocked.
  Operator configuration and exact local browser acceptance steps are in jordan.md.

All implementation stages A–G are complete. Remaining manual acceptance: actual browser
layout/keyboard/mobile checks, optional explicitly consented live provider request and
GitHub synchronization if sandbox networking blocks the final push. No Task 6B work,
ML training or academic report regeneration is included.
