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
19 focused Python checks (18 product, 1 retrieval runner) passed after correcting a
case-sensitive preview assertion; the real-document harness now has 38 passing cases.
This is browser-free integration, not visual verification. No landing styles changed.
