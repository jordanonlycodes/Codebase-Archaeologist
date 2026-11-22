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
