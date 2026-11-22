# Jordan — repository-aware engineering assistance

Jordan lives at `/workspace/jordan`. It investigates the **active source-free analysis**,
not a live checkout. No model training, source execution, embeddings, vector database,
new source retention or external retrieval is involved.

## Two modes, one evidence model

**Local intelligence** works offline without credentials. Browser modules
`jordan/retrieval.js` and `jordan/local.js` build one lexical/entity index per active
workspace lifecycle, using existing graph IDs, structural records and architecture
components. The existing `ArchaeologistImpact` index/query engine supplies membership,
cycle-safe traversal, original directed edges and representative evidence paths.
The local engine is directly reusable in Node. It is a deterministic investigation
interface with explicit supported intents, not unrestricted natural-language reasoning.
There is deliberately no local-question server API: browser snapshots do not exist on
the server, and local questions/evidence need not leave the browser.

**AI-enhanced mode** optionally explains a selected fact package using the implemented
OpenAI Responses provider. A replaceable `ExplanationProvider` protocol separates the
adapter from retrieval. No other provider or arbitrary OpenAI-compatible endpoint is
claimed. Only the configured server contacts `https://api.openai.com/v1/responses`.
No raw archive, whole analysis, full source body or conversation transcript is sent.
The question itself and selected facts can contain sensitive repository information.

## Supported investigations

| Investigation | Example |
| :-- | :-- |
| Overview / inventory | Summarize this repository. |
| Languages / function totals | What languages are used? How many functions were analyzed? |
| Structural review | Which functions are most complex? Show structural hotspots. |
| Model coverage | Which C functions have the highest model estimates? Which functions are unscored? |
| Entity facts | Explain `parse_config`. Explain `src/config.c`. |
| Directional relationships | Who calls `parse_config`? What does it call? What imports `lib/util.py`? |
| Components / cycles | Which components depend on `app`? Explain architecture cycles. |
| Two-file relationships | What relationships exist between `app/main.py` and `lib/util.py`? |
| Potential change impact | What could be affected if I change `parse_config` within 2 hops? |
| Missing information | What information is unavailable? |

Names in examples are illustrative: they must actually exist in the selected snapshot.
Quote exact paths/names for lookup. Partial quoted matches are supported; multiple
same-name or same-rank entities produce candidates with paths. Jordan never selects an
arbitrary ambiguous symbol. Unsupported requests explain supported investigations; an
unambiguous referenced/selected entity may still supply facts for optional cloud reasoning.

Rankings use retained function measurements, not guessed repository-wide totals. Missing
or truncated graph entities can reduce lookup/score coverage even when inventory counts
are available. An absence of relationships is not proof of independence. Graph resolution
rules and limitations remain those in [knowledge_graph.md](knowledge_graph.md).

## Direction, membership and evidence

CALLS means caller → callee; IMPORTS/INCLUDES mean source file → dependency. Upstream
queries reverse these edges; downstream follows them. File/component/directory selections
expand into existing bounded member seeds. Relationship answers distinguish external
reachability from observed relationships within membership (including recursion). CONTAINS/DEFINES do not propagate impact.
Impact defaults to one hop, supports explicit 1–3 hops and carries query coverage and
truncation. A Blast Radius launch carries origin, depth, direction and optional exact
target ID; Jordan retrieves that path again rather than trusting supplied source evidence.
See [blast_radius.md](blast_radius.md) for original traversal limits and semantics.

Each fact record retains an entity/edge ID, kind, name, optional relative path and line,
and bounded facts. Long disclosure names/paths are explicitly abbreviated with an
ellipsis; local inspection still accesses full retained identity/path. CALLS/import/include evidence retains original source → target IDs,
reference name, occurrence count and first available source location. Local records receive
E1…E12 display citations; cloud records receive those IDs **server-side** after schema
validation. Node inspection provides applicable structure, graph, impact and component
navigation. Full bodies and signatures are not retained, so Jordan cannot truthfully
explain implementation details or quote code. It does not invent feature attribution,
fixes, class definitions, runtime behavior or source snippets.

Retrieval is lexical, not embedding-based semantic search. Local answers are structured
synthesis over real metrics. Cloud instructions restrict repository claims to supplied
facts, categorize all repository strings and questions as untrusted data, and prohibit
following embedded instructions. No tools or code execution are available to the provider.
Unknown citation IDs, including unknown inline E identifiers, reject the explanation.
Valid IDs do **not** establish that every generated claim is supported. AI text is always
labeled as interpretation; absent citations are called out. All answers are rendered as
text, never executable HTML or unsanitized Markdown. Code/source generation is outside
this release's supported local investigations.

## Privacy and consent

Local mode makes no external AI calls. A same-origin capabilities request checks only
configuration status and contains no repository material. Switching to cloud mode does
not send evidence: submitting a question first produces its local answer and an exact
question/evidence JSON preview. The user must check consent and click **Send this evidence**
for each cloud request. Configuration alone is not consent. Remain local, mode switching,
unchecking consent during a request, cancellation and page teardown abort the browser
request and clear the pending disclosure. Data already sent cannot be recalled; cancellation
does not guarantee that remote computation stops. A failed request requires fresh consent
before retry. There are no automatic retries or silent fallback to cloud.

Cloud traffic travels browser → application server → OpenAI. `store:false` disables
Responses application-state storage, but is **not a promise of zero provider retention**;
review the provider's applicable data policies before disclosing sensitive facts. Keys
remain server-side and are excluded from configuration repr and API responses. Request,
prompt and provider-body logging is not added. Expected errors are scrubbed. Never put
credentials in a Jordan question or client-side storage.

The server validates a **client-supplied fact package**; it cannot independently verify
facts against a server snapshot because there is none. It assigns citation IDs from that
package and validates references, not factual entailment. No repository identifier is
used as authorization, and no repository/session cache or cross-user lookup is introduced.
The API is intended for the existing local trusted deployment. It is not an authenticated
public AI gateway: do not expose a configured instance to untrusted users without an
appropriate access/cost-control layer. Same-origin browser checks and bounded concurrency
are not authentication or an account quota.

Local history is at most eight local turns / 18 KiB, within the existing 32 KiB combined
UI preferences budget. It is keyed to the exact active snapshot in per-tab sessionStorage;
failed preference writes can leave conversation unsaved without losing the analysis.
A replacement, forget action, expired/missing pointer or new investigation clears the
applicable context. Logical expiration follows the snapshot's two-hour policy. Cloud
responses remain in page memory only, are excluded from persisted history and JSON
analysis export, and disappear on document reload. Local transcript/evidence remain
sensitive browser data: existing same-origin/browser-profile privacy boundaries apply.
No encryption or login is introduced. See [frontend.md](frontend.md).

## Configuration and API

No new dependencies. Local mode works with the normal README setup. Optional server env:

```bash
export JORDAN_CLOUD_ENABLED=true
export JORDAN_OPENAI_MODEL='YOUR_STRUCTURED_OUTPUT_CAPABLE_MODEL_ID'
read -rsp 'OpenAI API key: ' JORDAN_OPENAI_API_KEY; echo
export JORDAN_OPENAI_API_KEY
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
```

The example model is a placeholder, not a default or tested recommendation. The operator
must explicitly choose an available model supporting Responses structured outputs. An
invalid/missing enable flag, key or model makes cloud unavailable; no lazy network probe
occurs at startup. `.env.example` documents names but the app does not automatically load
`.env`. Disable cloud by unsetting `JORDAN_CLOUD_ENABLED` or setting it to `false` before
starting the server. Environment changes require restarting the running process.

- `GET /api/jordan/capabilities`: local/cloud availability, fixed provider label, limits,
  `source_bodies_retained:false`; no keys or configured model ID.
- `POST /api/jordan/explain`: JSON `{question, consent:true, evidence:[...]}`. Each evidence
  item has `entity_id`, `kind`, `name`, optional `path`/`line`, `facts:[{label,value}]`.
  Do not supply display citation IDs; the server assigns them. Extra fields are rejected.
- Response `{mode:"cloud", answer, citations:[{id,...factRecord}], limitations}`. Only
  actually cited evidence is returned. OpenAPI contains the precise typed contract.
- Errors retain `{error:{code,message}}`. Codes include `consent_required`,
  `origin_rejected`, `provider_unconfigured`, `provider_auth`, `provider_rate_limit`,
  `provider_timeout`, `provider_unavailable`, `provider_invalid_output`,
  `provider_output_limit`, `request_limit`, `evidence_limit`, `jordan_busy`.

Limits: 1,600 question characters, 12 evidence records, 16 facts/record, 256 characters per
value/name/path/ID, 64 per fact label, 24 KiB evidence and 32 KiB request (UTF-8, counted
while reading before JSON parsing), two active cloud requests/process, 10s request-read
budget, 5s connection / 30s read / 45s total provider budget, 64 KiB provider response,
1,800 output tokens and 6,000 answer characters. Client aborts after 50s. Provider env
proxies and redirects are disabled. No user-supplied hosts/endpoints or unbounded retry
policy exist. Original analysis/graph/impact bounds remain unchanged.

The adapter follows the official [Responses create contract](https://developers.openai.com/api/reference/resources/responses/methods/create)
and [structured outputs guide](https://developers.openai.com/api/docs/guides/structured-outputs),
consulted for this implementation. Provider output format/model support must match the
operator's configuration. Live provider availability is not implied by mocked tests.

## Scientific boundaries

Complexity and hotspots are calculated structural signals. Potential impact is static
reachability, not predicted breakage. C-only Random Forest estimates are uncalibrated
research signals, neither confirmed vulnerabilities nor reliable correctness verdicts.
Python and missing-model functions remain unscored. No averaged file/repository defect
probability is manufactured. Source code understanding beyond retained structural facts,
dynamic import/call resolution, automatic fixes, semantic embeddings and history-based
analysis are not implemented.

## Verification and local acceptance

Run the full existing suite following README (including the documented sandbox selector
workaround if needed), plus targeted checks:

```bash
.venv/bin/pytest tests/test_jordan.py tests/test_jordan_frontend.py tests/test_product.py -q
node tests/frontend/jordan.test.cjs
node tests/frontend/workspace.test.cjs
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Import a mixed C/Python ZIP at `/explore`, then:
1. Open Jordan and ask a summary, language count, complexity ranking and “Who calls it?”.
2. Inspect citations and follow a real function into structure/graph/impact; return without
   uploading again. Try duplicate function names, Python-only and empty repositories.
3. Launch from an actual impact path; compare its direction/depth/lines against source.
4. Without configuration, confirm local operation and unavailable cloud control. With an
   operator-configured provider, review the exact preview, decline once, then explicitly
   consent to a small safe disclosure. Check failure/cancel/withdrawal behavior. This live
   provider check has not been performed in the development sandbox.
5. Verify keyboard flow, Ctrl/Command+Enter, native context/evidence disclosure panels,
   1366×768, tablet/mobile, reduced motion, long names, literal HTML text and console.
6. Navigate/back/refresh, replace/forget the repository, test expiry and storage denial.
   No stale answer should survive snapshot replacement. Cloud answers should not restore.

Exact final automated counts and smoke results are recorded in task6a_progress.md.
Browser attempts here failed before rendering: Chromium exit 133 (`setsockopt: Operation
not permitted`), Firefox exit 139. No visual/responsive/FPS or live cloud success is claimed.
