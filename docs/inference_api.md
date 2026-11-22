# C-function inference API (Task 3A)

## Current interface — Task 5

The analysis endpoints and response schemas remain unchanged. Import lives at `/explore`;
C-only model results live at `/workspace/risk`. Other dedicated workspaces hydrate the
same source-free, expiring browser snapshot without further API analysis requests.
There is no server-global repository store or snapshot-ID authorization endpoint.
See [frontend storage, isolation, routes and lifecycle](frontend.md). Model loading,
trusted artifact requirements and interpretation below remain applicable.

`POST /api/analyze` still accepts one multipart `file` ZIP. Static analysis, exclusions, security limits and error responses are unchanged. A successful response adds `defect_risk` to schema 1.0 as an additive field, with its own schema version `1.0`. OpenAPI defines the nested dataclass contracts in `app/ml/schemas.py`. Export JSON downloads this same response including all functions and file issues; no source text or server paths are included.

## Contract

| Field | Meaning |
| --- | --- |
| status | `ready`, `partial`, `unavailable`, or `no_functions` |
| message | Safe user-facing status explanation |
| model_version | Validated artifact version, or null |
| analyzed_functions | Functions with successful predictions |
| defect_related / non_defect_related | Successful class 1 / class 0 predictions |
| skipped_functions | Extracted definitions with no prediction; excludes unknown counts |
| eligible_files | Included files whose suffix is exactly `.c`; `.C` is not treated as C |
| unsupported_source_files | Included source files outside `.c` scope; not a function count |
| functions | Bounded list of genuine extracted definitions |
| file_issues | Relative path and reason for incomplete coverage |

Each function has `name` (nullable), repository-relative `path`, 1-based inclusive `start_line`/`end_line`, `status`, nullable `predicted_class` (0/1), nullable `model_probability` (label-1 probability in [0,1]), and ordered `features` with the exact Task 2 names. Missing feature values serialize as null, never NaN. Line endings are normalized; ZIP wrapper folders are retained in paths. Source code is not returned.

Function statuses include `analyzed`, shared extractor parse statuses, `function_size_limit` and `inference_failed`. Failed functions have no prediction or probability. Missing model returns `unavailable`, empty function results, and zero **successfully analyzed** functions; it does not assert that the repository has no functions. With no eligible `.c` files, the service returns `no_functions` without loading a model. A valid C file containing only declarations also returns `no_functions`.

Malformed files report file issues. Independently parseable function definitions inside them may be scored. Entirely unparsed files, size exclusions or exhausted workload limits have unknown function counts. The UI exposes these separately. There is no C++/Python/Java/JavaScript ML inference. Header-only definitions are outside this release's `.c` scope.

## Runtime and resource policy

The static scanner first determines eligible included text files. Inference runs before the extracted temporary directory is removed. Tree-sitter discovers definitions and declarator-based names. Each function uses unchanged `extract_features`; rows preserve `FEATURE_NAMES` ordering and float64 dtype. The persisted sklearn pipeline supplies the original imputer and Random Forest. Model `predict` provides classes and `predict_proba` supplies label-1 scores. Output shape, classes and finite probability range are checked before exposing results.

Per analysis: at most 1,000 definitions, 512 KiB per C file, 8 MiB of C source parsed, and 128 KiB per scored function. Counts and byte limits bound workload; this is not a hard CPU deadline. Remaining files/functions receive explicit limit issues, and no total is guessed. Existing upload admission limits allow two analyses per process. One lazily loaded model is shared per process, with a lock around first initialization; the model is not fitted or mutated during requests. Workers each load their own model. UI interactions reuse results.

`ARCHAEOLOGIST_MODEL_DIR` is an operator-only setting, defaulting to project-relative `artifacts/devign-v1`. Only this path is passed to trusted joblib loading. The upload never selects it. Joblib can execute code, so schema/checksum checks do not make an untrusted artifact safe. Do not configure this directory from user content.

Loading checks feature schema/version/order, Tree-sitter versions, exact recorded numerical-library versions, binary SHA256, dimensions, classes, selected classifier type, model version and probability support. Errors are sanitized in API results. A missing optional package also yields model unavailable. Failure is cached until restart. The app imports and static routes work with only base dependencies installed.

## Recovery and local diagnosis

Restore a trusted matching `pipeline.joblib`, `metadata.json`, and `feature_schema.json`; install the recorded environment from `requirements-ml-frozen.txt` on matching Python. Restart the server after changing artifacts or configuration. Raw/processed data is not needed for inference. The following local diagnostic reveals the precise compatibility exception to the operator without exposing it through the API:

```bash
source .venv/bin/activate
python - <<'PY'
from app.ml.repository import SERVICE
from app.ml.model_store import load_pipeline
pipeline, metadata = load_pipeline(SERVICE.directory, trusted=True)
print(metadata['model_version'], type(pipeline.steps[-1][1]).__name__)
PY
```

Never download and deserialize a model from an uploaded archive. If artifacts are permanently lost, follow the explicit offline Task 2 reproduction instructions; do not run training from the server.

## Interpretation and verification

Scores estimate Devign label 1 from syntax patterns, without calibration or attribution. Class 0 does not prove safety. Counts and review ranking are not an aggregate repository probability. The recorded test F1 0.526 and ROC-AUC 0.587 indicate modest signal; false positives, missed defects, shared-project data and deployment shift limit reliability. Benchmark evaluation scored parse failures with imputation; live analysis abstains, so coverage differs.

Run `python -m pytest -q` for all regressions or `python -m pytest -q tests/ml/test_repository.py` for focused integration tests. These new tests do not fit estimators or use raw datasets. Actual artifact tests explicitly skip if the ignored local artifact is absent; parser tests skip if optional dependencies are absent. The full existing suite includes two preserved tiny Task 2 fitting tests on authentic training rows. It never reruns the held-out evaluation. In socket-restricted sandboxes use the documented selector wrapper in `ml_pipeline.md`.

Browser verification remains pending in the restricted development sandbox: Uvicorn completed startup but could not bind localhost, and headless Chromium failed `setsockopt: Operation not permitted`. API tests exercise the real FastAPI stack in-process, including genuine predictions, preserved metrics, schema, assets and JSON export wiring.

## GitHub ingestion

Task 4A.1 adds `POST /api/analyze/github` with a public repository URL. It downloads a pinned default-branch ZIP, then invokes the same archive/static/inference function as upload analysis. The additive `source` object records ZIP filename or GitHub provenance; top-level `analyzed_at` is the analysis timestamp. C-only scope, workload limits, model caching and missing-model behavior are identical. See [GitHub ingestion](github_ingestion.md).

## Structural metrics (Task 4A.2)

The optional additive `structural` response has independent source-calculated metrics and coverage. Static analysis never requires loading the model. Request-local C file trees can be reused for extraction, while original per-function ML features and predictions are preserved. `structural.functions[].ml_result_index` points into the existing `defect_risk.functions` only for unique path/line-range/name matches; unmatched/Python functions remain ML-unavailable. See [structural definitions and contracts](structural_intelligence.md). Complexity hotspots are separate from uncalibrated ML scores.

### Knowledge graph response

Both analysis endpoints also return optional `knowledge_graph` schema `1.0`, containing
nodes, directed edges, unresolved references, summary, coverage and limits. Existing
structural and ML fields retain their meaning. C function nodes link the same structural
ID and actual `ml_result_index`; no other language receives a model score. JSON export
includes the component automatically. See [knowledge graph](knowledge_graph.md) for
edge directions, conservative resolution rules and resource bounds. No graph-specific
endpoint or persistent storage is introduced.

### Architecture and heatmap response (Task 4C.1)

Both existing analysis endpoints add optional `architecture`, schema `1.0`. It contains
`components`, directed aggregated `edges`, parent-linked `heatmap` nodes,
`dependency_cycles`, evidence-based `findings`, `summary`, `coverage`, `definitions` and
`limits`. It reuses existing inventory, structure and graph outputs; existing fields
and the whole-result JSON export remain available. No new endpoint/storage is required.

Component counts cover immediate member files; heatmap directories aggregate descendants.
Complexity uses explicit maxima/sums of valid structural measurements. Nullable fields
and `measured_files` distinguish missing coverage from zero. `max_c_function_score` is
only the maximum existing C-function estimate, never a file/directory defect probability.
Aggregate graph-edge counts differ from source occurrences; bounded edge-ID samples
link to original knowledge-graph evidence. See [architecture contracts and limits](architecture_heatmaps.md).


### Optional browser impact export (Task 4C.2)

Analysis endpoints remain unchanged. Blast Radius queries run locally over the retained
`knowledge_graph`, `architecture` and `structural` data using the shared JavaScript
engine. Browser JSON export preserves every API field and adds `blast_radius` (schema
`1.0`) only when an impact origin is selected. It contains origin/depth/direction,
bounded seeds, direction-specific reachability/path records, original edge evidence,
internal seed relationships, attributable uncertain references, summary, coverage and
limits. Clearing focus omits it on the next export. There is no persistent impact
store or new server endpoint. See [contract, examples and limits](blast_radius.md).
