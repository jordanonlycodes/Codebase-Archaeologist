# Codebase Archaeologist

A local repository intelligence dashboard built with FastAPI, Jinja2, vanilla JavaScript and custom CSS. Upload a repository ZIP or import a public GitHub URL to inspect real file, language and line metrics. Uploaded code is **never executed**.

Task 1 provides the repository dashboard. Task 2 adds an optional, reproducible C-function research pipeline using the official CodeXGLUE/Devign splits. A Random Forest was trained locally and evaluated once on the official test holdout. Task 3A integrates that saved model into ZIP analysis and a C-only Defect Risk Intelligence dashboard. Task 4A.1 adds public GitHub default-branch snapshot imports through the same analysis pipeline. Tasks 4A.2–4B.2 add structural metrics, a repository knowledge graph and a shared 2D/3D explorer.

## Install on Ubuntu

Requires Python 3.10 or newer. Ubuntu 22.04 or newer provides a suitable Python version.

```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip git
cd /path/to/codebase-archaeologist
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

The 2D graph explorer needs no additional packages. For optional locally served 3D
assets, run `python tools/install_graph_assets.py` once with network access; see
[explorer setup](#interactive-knowledge-graph-explorer-task-4b2). Node.js 18+ is needed
only for the frontend tests, not to run the application.

Package installation requires access to PyPI. Static analysis needs no database, credentials, Node build, containers or ML packages. C-function predictions require the optional ML dependencies and trusted local artifacts. Dashboard assets are local; the optional Swagger API documentation uses FastAPI's default CDN assets. The optional training dependencies and commands are documented below.

## Run

From the project directory:

```bash
source .venv/bin/activate
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Open **http://127.0.0.1:8000**. Select or drop a ZIP; analysis starts immediately. Progress reflects bytes uploaded, followed by an indeterminate validation/scanning/C-inference state. Results include searchable, sortable, paginated files and a JSON download. New failures retain the previous successful analysis with an explicit notice.

Use this as a local, single-user application. Two analyses per process may run concurrently; additional requests receive `429`. Normal completion and handled failures remove uploaded/extracted temporary files. A process crash or forced termination may leave OS temporary files; normal OS temporary-directory cleanup still applies. Results are held in browser memory, not persisted.

## API

- `GET /` — dashboard.
- `GET /api/health` — health response.
- `POST /api/analyze` — one multipart file named `file`, containing a `.zip` archive.
- `POST /api/analyze/github` — JSON `{ "url": "https://github.com/owner/repository" }` for public repositories.
- `GET /docs` — interactive OpenAPI documentation.
- `GET /openapi.json` — machine-readable API schema.

```bash
curl --fail-with-body -F 'file=@/path/to/repository.zip' \
  http://127.0.0.1:8000/api/analyze > analysis.json
```

The versioned response (`schema_version: "1.0"`) includes `repository`, `analyzed_at`, `archive_entries`, `summary`, `languages`, `files`, `largest_files`, `skipped` and metric-definition `notes`. Each file includes its relative path, language, source classification, byte count, line totals, blanks and nullable comment/code counts. Repository file contents are never returned.

Errors have a consistent shape:

```json
{"error": {"code": "unsafe_archive", "message": "Archive contains an unsafe path."}}
```

Expected statuses: `400` invalid/unsafe archive or multipart request; `408` upload timeout; `413` safety limit; `415` unsupported request/file; `422` missing file or no supported text; `429` capacity; `500` unexpected server failure. Uploaded filenames and paths are rendered as text in the dashboard, never interpreted as HTML.

## Safety and limits

Limits are centralized in `app/config.py`:

| Limit | Value |
| --- | --- |
| ZIP upload | 25 MiB |
| Entire multipart request | 26 MiB |
| Expanded archive | 100 MiB |
| Individual archive entry | 2 MiB |
| Archive entries, including directories | 5,000 |
| Path depth / UTF-8 path length | 30 components / 240 bytes |
| Per-entry compression ratio | 200:1 |
| Upload deadline | 120 seconds |

Limits include entries that will later be excluded. Remove dependencies/builds/large assets before uploading if necessary. The request boundary checks actual bytes before multipart parsing, even without an accurate `Content-Length`. It bounds concurrent request bodies and prevents unlimited multipart files/fields. Analysis runs off the async request loop.

The extractor preflights central-directory metadata before allocating ZIP entries, validates every path and entry before creating files, rejects traversal, absolute/drive/backslash/control-character paths, duplicate/case-colliding file paths, file/directory conflicts, symlinks, devices and other special files. It rejects encryption, split/ZIP64 archives and compression other than stored/deflate. Extraction streams bounded chunks into a new private temporary directory; it does not use `extractall`, preserve executable bits or invoke repository programs. Unsupported binary content and nested archives are skipped, never unpacked recursively.

## Metric definitions

- **Included files:** UTF-8 text files, including source, documentation and configuration. UTF-8 BOM is accepted. Binary/control-byte and non-UTF-8 files are skipped.
- **Directories:** visited, non-excluded directories including empty ones; excludes the temporary extraction root. A repository wrapper folder inside the ZIP remains part of paths and totals.
- **Language composition:** extension/name-based classification, grouped by included file count. It is not a parser-based assertion about file validity. Unknown text is labeled `Other text`.
- **Total lines:** physical text lines, including blanks. LF, CRLF and CR are supported. A final newline does not create an extra line; an empty file has zero lines.
- **Source lines:** physical lines in recognized source files, including their blanks and comments. Documentation, data and configuration are excluded. This is not a pure executable-code LOC count.
- **Blank lines:** lines containing only whitespace.
- **Known comment lines:** comment-only lines in tokenizable Python. Python inline comments stay on code lines; docstrings are code/string lines. Standard JSON has zero comments by definition. Other languages and un-tokenizable Python return `null` for comment/code metrics. Coverage is displayed; the partial total must not be treated as a whole-repository count.
- **Largest files:** top five included text files by actual byte size.
- **Skipped files:** counts by reason. Directory ZIP entries are not counted as skipped files.

Exclusions include `.git`, `node_modules`, `vendor`, virtual environments (also detected via `pyvenv.cfg`), build/dist/target outputs, caches and binary/archive extensions. The complete policy and language map live in `app/analysis/policy.py` and `app/analysis/languages.py`. This conservative foundation does not evaluate `.gitignore`, decode legacy encodings, inspect dependencies for CVEs or perform semantic vulnerability detection.

## Project structure

```text
codebase-archaeologist/
├── app/
│   ├── main.py                 # FastAPI assembly and error handling
│   ├── config.py               # Archive limits
│   ├── errors.py               # Expected domain failures
│   ├── middleware.py           # Upload byte/concurrency boundary
│   ├── routes/
│   │   ├── dashboard.py        # Dashboard and health
│   │   └── analysis.py         # Multipart API and temp-file lifecycle
│   ├── ingestion/
│   │   └── archive.py          # ZIP validation and bounded extraction
│   ├── analysis/
│   │   ├── models.py           # Versioned result dataclasses
│   │   ├── scanner.py          # Recursive inventory and aggregation
│   │   ├── languages.py        # Language/source classification
│   │   ├── lines.py            # Physical line and comment metrics
│   │   └── policy.py           # Directory and binary exclusions
│   ├── ml/
│   │   ├── inference.py        # Repository and C-function contracts
│   │   ├── acquire.py          # Pinned official data and license snapshots
│   │   ├── dataset.py          # Schema validation, auditing and cleaning
│   │   ├── features.py         # Shared Tree-sitter C features
│   │   ├── prepare.py          # Development features and EDA
│   │   ├── eda.py              # Plots and machine-readable statistics
│   │   ├── estimators.py       # Three fixed sklearn pipelines
│   │   ├── evaluation.py       # Metrics and validation selection
│   │   ├── train.py            # Checkpointed training and single test pass
│   │   ├── model_store.py      # Artifact integrity and compatibility
│   │   ├── c_model.py          # Explicit offline C-function inference
│   │   ├── report.py           # Reports from saved results
│   │   └── io.py               # Checksums and atomic JSON records
│   ├── templates/dashboard.html
│   └── static/{app.js,styles.css,mark.svg}
├── tests/
│   ├── conftest.py
│   ├── test_archive.py
│   ├── test_scanner.py
│   ├── test_api.py
│   ├── test_middleware.py
│   └── ml/                    # Features, leakage, metrics, artifacts
├── docs/ml_pipeline.md
├── reports/ml/                # Actual EDA, plots and model results
├── data/                      # Ignored raw/processed data
├── artifacts/                 # Ignored trained pipelines/checkpoints
├── .gitignore
├── pytest.ini
├── requirements.txt
├── requirements-ml.txt
├── requirements-ml-frozen.txt
└── README.md
```

## Verification

```bash
source .venv/bin/activate
python -m pytest -q
python -m pip check
python -c 'from app.main import app; print(app.title)'
python -m compileall -q app tests
```

The tests include a real mixed-language fixture with **4 included files, 2 source files, 4 included directories, 10 total lines, 6 source lines, 2 blanks, 1 known comment line and 4 skipped files**. They verify language shares, byte totals, API serialization, unsafe paths, symlinks/special files, duplicate paths, compression bombs, corruption, forged metadata, limits, binary exclusion, no execution and temporary-file cleanup after both success and failure. Small injected limits keep security tests fast without allocating huge archives.

For a live smoke test, start Uvicorn, then upload a repository ZIP with the `curl` command above. The automated API tests exercise the real ASGI application without an external server.

Task 1 verification: **73 tests passed** on Python 3.14.10 with FastAPI 0.165.0. Dependency checks, Python compilation, Python 3.10 grammar checks, JavaScript syntax and template rendering also passed. The installed Starlette version emits one upstream deprecation warning for its httpx-based test client. In the restricted build sandbox, tests required bounded event-loop polling because socket-based thread wake-ups were blocked; no application behavior was patched. Uvicorn completed application startup, but the sandbox denied local port binding. A Chromium preview was also blocked by socket restrictions, so live HTTP and visual browser verification remain outstanding on a normal local terminal.

## Task 2: dataset, features and training

The source is [google/code_x_glue_cc_defect_detection](https://huggingface.co/datasets/google/code_x_glue_cc_defect_detection), pinned to revision `69bd48c03223c2104342acd9a807caf61ac3efb8`. The actual Parquet schema is `id: int32`, `func: string`, `target: bool`, `project: string`, `commit_id: string`. The provider declares **C-UDA** for the dataset; its dataset card, agreement text and source checksums are preserved locally. The MIT license on CodeXGLUE's software is a separate declaration.

| Split | Official rows | Rows used | Label 0 / Label 1 used |
| --- | ---: | ---: | ---: |
| Train | 21,854 | 21,750 | 11,786 / 9,964 |
| Validation | 2,732 | 2,723 | 1,539 / 1,184 |
| Test | 2,732 | 2,732 | 1,477 / 1,255 |

No missing fields were found. Cleaning quarantined all records in 54 contradictory development function groups and excluded 5 development functions matching test functions: 113 development rows removed in total. Cross-split identical-function overlap is zero after cleaning. The test set retains its one contradictory duplicate group. Shared commits and possible near duplicates remain a generalization limitation. Every removal has a recorded ID, hash and reason; no label is invented or changed.

The shared `c-function-v1` extractor measures 11 features: physical lines, nonblank lines, function bytes, parameter count, conditional count, loop count, return count, maximum control nesting depth, approximate decision complexity, pointer syntax count and call count. Tree-sitter C parses source without execution. Parse errors retain lexical metrics and set structural metrics to missing. The training pipelines fit median imputation on training rows only; Logistic Regression also uses scaling. Metadata is never a predictive input.

Install and reproduce from the project directory:

```bash
source .venv/bin/activate
python -m pip install -r requirements-ml.txt
python -m app.ml.acquire
python -m app.ml.prepare
python -m app.ml.train
python -m app.ml.report
python -m pytest -q
```

The acquisition command resolves an immutable revision on first use, caches the three official Parquet files and licensing information, then verifies checksums on reuse. To reproduce the exact recorded dataset revision in a fresh checkout, follow the pinned-manifest procedure in [the pipeline guide](docs/ml_pipeline.md#reproducing-the-recorded-source). `requirements-ml-frozen.txt` records the successful Python 3.14.10 environment; on the same Python version, install that file for exact package versions. The broader optional requirements permit compatible local environments, but binary model loading requires the recorded versions.

The complete experiment fits each of three fixed configurations once with seed 42 and threshold 0.5. Selection uses validation F1, with recall, false positives and training/validation gap as documented tie-breakers. The selected pipeline is not refitted on validation data. The test set is evaluated once after selection. Completed runs are verified and reused on repeated commands; interrupted test evaluation is never automatically repeated.

| Model | Validation accuracy | Precision | Recall | F1 | ROC-AUC |
| --- | ---: | ---: | ---: | ---: | ---: |
| Logistic Regression | 0.5454 | 0.4707 | 0.3657 | 0.4116 | 0.5372 |
| Random Forest | 0.5685 | 0.5035 | 0.5397 | 0.5210 | 0.6068 |
| HistGradientBoosting | 0.5487 | 0.4820 | 0.5093 | 0.4953 | 0.5746 |

**Selected: Random Forest.** Its untouched-test accuracy is **0.5553**, precision **0.5153**, recall **0.5378**, F1 **0.5263** and ROC-AUC **0.5874**. Confusion matrix `[[TN, FP], [FN, TP]]`: `[[842, 635], [580, 675]]`. Training F1 was 0.7334 versus validation 0.5210, indicating overfitting. These modest results do not establish a practical vulnerability detector; test-label prevalence alone gives an always-negative accuracy of 0.5406, and an always-positive predictor has higher F1 at the cost of a 100% false-positive rate.

Actual plots, descriptive statistics, comparisons and evaluation records are in [reports/ml](reports/ml/README.md). The selected pipeline is `artifacts/devign-v1/pipeline.joblib`; schema, package versions, parameters, checksums and selection records are stored beside it. Raw data, processed matrices and model binaries are ignored by Git. The six report plots and small JSON reports are tracked.

Verification: **120 tests passed** (73 existing application tests plus 47 targeted ML tests), including deterministic extraction, leakage prevention, actual model serialization/loading and reproducibility on 128 authentic training records. No synthetic labels were used to train or evaluate models. Cleaning/metric unit fixtures test mechanics only. One existing upstream Starlette/httpx deprecation warning remains. See [the pipeline guide](docs/ml_pipeline.md) for the sandbox test runner and failure recovery.

## Task 3A: real C-function defect intelligence

The ZIP API now adds `defect_risk` while preserving existing inventory and static metrics. Eligible lowercase `.c` files are parsed with Tree-sitter. Genuine function definitions are scored with the unchanged Task 2 features and saved Random Forest pipeline. No training, dataset access, uploaded model loading or code execution occurs during analysis.

The black-and-crimson dashboard includes actual analyzed/class/skipped counts, searchable and paginated function results, class and score distributions, findings grouped by file, review priorities, and a feature detail panel. Charts use accessible native progress bars; no Chart.js installation or CDN is needed. JSON export includes the full ML result. Searching, sorting, selecting and navigation reuse the response without inference requests.

### Enable inference

```bash
source .venv/bin/activate
# Install the recorded environment when using the existing model (Python 3.14.10).
python -m pip install -r requirements-ml-frozen.txt
# Optional: defaults to artifacts/devign-v1 relative to the project, not the shell cwd.
export ARCHAEOLOGIST_MODEL_DIR=/absolute/path/to/trusted/devign-v1
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000 and choose a repository ZIP containing `.c` files. The model loads once on the first eligible request in each server process. Package versions, feature schema/order, binary checksum, classifier type and class labels are validated. The operator-configured directory is trusted: **never point it at uploaded or untrusted content**. A failed load is cached until server restart. Missing, corrupt or incompatible artifacts produce a visible unavailable state; static results remain functional.

Restore `pipeline.joblib`, `metadata.json` and `feature_schema.json` together from a trusted backup of `artifacts/devign-v1/`, install matching recorded package versions and restart. Git intentionally does not include model binaries; cloning alone does not enable predictions. Recovery does not require raw datasets. If no trusted artifact exists, reproducing Task 2 is a separate explicit offline operation; the application never trains automatically. See [the inference API guide](docs/inference_api.md) for limits, statuses and diagnostic commands.

Scores are **uncalibrated estimated model probabilities**, not confirmed vulnerabilities, severity or repository risk. Python, C++, JavaScript and other languages receive static analysis only. Unknown function counts from unreadable/limited files are reported as file issues, not invented skipped-function totals. Live inference abstains on invalid functions; benchmark evaluation included parse failures with imputation, so its coverage differs. The existing modest held-out performance remains unchanged.

Task 3A verification: **140 passed, 0 failed, 0 skipped** including all 120 earlier tests and 20 inference/integration cases. New tests only load saved artifacts or use explicit test doubles; they never fit a model or access the dataset. The preserved Task 2 regression tests still perform their two tiny authentic-subset Logistic Regression fits. No full model training or held-out evaluation was rerun. The real ZIP API smoke test scored two C functions alongside Python/C++ files. JavaScript syntax and dependency checks passed. Uvicorn startup succeeded but local port binding was blocked; Chromium also failed with a sandbox socket permission error, so visual/browser interaction verification remains outstanding.

Task 3B's academic report is linked below. Future work includes independent-project evaluation, calibration, and the planned Task 5 visual redesign. No aggregate repository probability or invented feature attribution is provided.

## Academic report (Task 3B)

The [submission PDF](submission/Codebase_Archaeologist_Report.pdf) and [editable DOCX](submission/Codebase_Archaeologist_Report.docx) document Tasks 1, 2 and 3A for Bilal Malik (24P-3061), FAST-NUCES, Peshawar. The report covers dataset provenance, preprocessing, genuine EDA, exact recorded validation/test metrics, architecture, implementation, testing and limitations. Future features are explicitly identified as proposals; no academic-report generation step retrains or evaluates a model.

Regenerate both formats from the same content source using the existing ML plotting dependencies:

```bash
.venv/bin/python tools/generate_report.py
```

The generator uses Matplotlib/Pillow and standard-library Office Open XML packaging; it requires no extra application dependencies or remote downloads. Saved evidence comes from `reports/ml/`; local artifact metadata is cross-checked when present. [Report manifest](submission/report_manifest.json) records source hashes and document metadata. See [submission notes](submission/README.md) for document validation and rendering limitations. The full premium README redesign remains future Task 5 work.

## Public GitHub imports (Task 4A.1)

Choose **Import from GitHub**, enter `https://github.com/owner/repository`, then select **Analyze Repository**. Leading/trailing whitespace, a trailing slash and one `.git` suffix are normalized. Only public repositories and the default branch are supported; tokens, private repositories, branch selection and Git history are outside this release. Results use the existing static and C-only ML dashboard and JSON export. Source metadata includes a canonical GitHub link, verified default branch and exact downloaded commit; `analyzed_at` remains the analysis timestamp. ZIP provenance keeps the original filename.

```bash
curl --fail-with-body -H 'Content-Type: application/json' \
  -d '{"url":"https://github.com/octocat/Hello-World"}' \
  http://127.0.0.1:8000/api/analyze/github > github-analysis.json
```

A plain HTTPS GitHub repository URL is required. Credentials, ports, non-GitHub/lookalike hosts, encoded paths, query strings, fragments and file/issue/PR paths are rejected. The server constructs fixed GitHub API requests, resolves the default branch to a commit, then requests its ZIP archive. Automatic redirects and environment proxies are disabled; every allowed redirect must target the same repository/commit on `codeload.github.com` over HTTPS. Standard TLS verification remains enabled. Downloaded code is never executed or installed.

`GitHubLimits` in `app/config.py` sets 10-second connect/read timeouts, a 60-second total acquisition deadline, at most 3 redirects, 256 KiB metadata, a 4 KiB JSON request and a 25 MiB streamed archive cap. Existing extraction limits still apply: 100 MiB expanded, 2 MiB per file, 5,000 entries, depth 30, ratio 200:1. GitHub and ZIP requests share the existing two-analysis admission limit. Temporary archives and extracted files close on success/failure. No new environment variables or dependencies are needed. The existing optional `ARCHAEOLOGIST_MODEL_DIR` setting still controls trusted inference artifacts.

Not-found/private/empty repositories, rate limits, timeouts, network failures, oversized archives and unsafe/corrupt ZIPs return structured errors. Rate limiting is surfaced without automatic retries; retry later. Renamed repositories that redirect at the metadata API should be submitted using their current canonical URL. See [GitHub import API and manual checks](docs/github_ingestion.md).

## Structural Intelligence (Task 4A.2)

ZIP uploads and GitHub imports now include `structural` results and a dedicated dashboard section: C (`.c`, Tree-sitter) and Python (`.py`/`.pyi`, standard-library AST) function metrics, cyclomatic complexity, control nesting, spans/parameters, file/repository aggregation, code composition, stable snapshot-local identifiers and transparent review hotspots. Static structural analysis remains available without the Random Forest. Unsupported source languages and incomplete/limited parses report explicit coverage; unavailable metrics remain null.

The UI offers complexity bands, classified-line composition, file rankings, review reasons and a searchable/sortable 25-row function view. JSON export includes all bounded structural records, coverage, definitions and configured thresholds. Complexity bands are 1–5 / 6–10 / 11–20 / 21+; hotspot thresholds are complexity ≥11, nesting ≥4, span ≥80 lines or parameters ≥6. These are review heuristics, not defect probabilities or software-quality scores.

Limits in `app/config.py`: 512 KiB/file, 8 MiB source, 128 KiB/function, 2,000 definitions, 100,000 visited AST nodes/file and 400,000 total node visits. Existing ingestion protections remain in force. No new dependencies are required for Python; C uses the existing optional Tree-sitter installation. See [structural metric definitions, coverage and manual verification](docs/structural_intelligence.md). Run `python -m pytest -q tests/test_structural.py` for focused checks. The trained feature schema, model artifacts and academic report remain as previously recorded.

### Repository knowledge graph (Task 4B.1)

ZIP and public GitHub analyses now include `knowledge_graph` in their API response
and JSON export: repository/directory/file/function hierarchy, supported C/Python
calls, Python imports and C includes. It reuses structural IDs, metrics, hotspot
reasons and actual C-only ML results. Ambiguous/dynamic references and bounded coverage
are explicit; no external definitions or runtime guarantees are invented.

See [graph engine documentation](docs/knowledge_graph.md) for resolution rules,
resource limits, schemas, a verified example and `GraphIndex` query helpers.
Run `pytest tests/test_graph.py -q` or the full `pytest -q` suite.
The Task 4B.2 explorer below consumes these retained results.

### Interactive Knowledge Graph Explorer (Task 4B.2)

The explorer uses actual `knowledge_graph` results from ZIP and GitHub analyses.
Search spans all retained entities, including hidden functions; selecting a result
opens a bounded neighborhood. Node inspection includes identity/source details,
applicable structural metrics, hotspot reasons, genuine C-only ML estimates,
incoming/outgoing links, call-site evidence and unresolved references. JSON export
retains the backend graph independently of visualization filters.

| Perspective | Automatic layout | Relationships |
| --- | --- | --- |
| Repository Knowledge Graph | Packed containment hierarchy | Repository → directory → file → function |
| Function Call Graph | Directed layers; recursive groups share a layer | Resolved caller → callee |
| Dependency Graph | Clusters by actual directory path | Importing/including file → dependency |

Choose **Automatic**, **Hierarchical** or **Radial** layouts. Explicit Hierarchical
uses containment in Knowledge and directed layers in Calls/Dependencies. Collapse or
expand selected directory/file groups, focus a branch, or explore one/two hops with
incoming/outgoing highlighting. Perspective changes explicitly reset incompatible
entity/relationship/language filters. Layout, overlay and selection are shared across
renderers where applicable; switching renderers never reanalyzes the repository.

- **2D:** dependency-free SVG with retained elements, collision-aware spacing,
  contextual labels, pointer-anchored zoom, panning, dragging and keyboard selection.
- **3D:** locally served **3d-force-graph 1.73.3**, including Three.js, with fixed spatial
  layouts, orbit/pan/zoom, dragging, camera focus and idle/offscreen rendering pauses.
- **Overlays:** entity type, measured structural complexity/hotspots and actual C-only
  ML predictions. Unavailable values remain unscored; neither metrics nor model scores
  establish confirmed defects or vulnerabilities.

Both modes provide fit/reset, fullscreen or expanded view, filters and the same
inspector. Rendering is bounded to **180 nodes / 420 edges**, with displayed/retained
counts, collapsed-group counts and backend coverage. Large knowledge views initially
collapse file groups. SVG updates are batched; 3D avoids unchanged graph submissions
and uses a fixed conservative graphics profile. There is no quality-preset selector.

#### Explorer setup and rendering preferences

2D works immediately with local assets. To install the optional 3D bundle:

```bash
source .venv/bin/activate
python tools/install_graph_assets.py
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

The installer pins the package version, preserves its MIT license and writes a hash
receipt. No npm build or runtime CDN request is required. If the bundle is missing,
WebGL is unavailable or renderer initialization fails, the explorer reports the issue
and falls back to 2D. Fine-pointer desktops at least 1000px wide prefer 3D when WebGL
is detected and reduced motion is off; other devices start in 2D. Users can switch
modes. Reduced motion disables camera transitions.

Initial asset acquisition was blocked by sandbox DNS. During refinement, a local
bundle was present and matched its receipt; it was preserved unchanged. Browser/GPU
operation remains unverified here because Chromium startup was blocked. The latest
implementation verification recorded **354 Python tests and 21 frontend cases passing**
(0 failed, 0 skipped; the Python suite includes the frontend runner). These results
verify contracts and mocked adapters, not measured FPS, latency or visual quality.

```bash
node tests/frontend/graph.test.cjs  # Node.js 18+, no npm packages
pytest -q
```

See [graph algorithms, limits and local performance checks](docs/knowledge_graph.md#interactive-explorer-task-4b2)
and [development history](docs/development_history.md) for the original problems,
implemented solutions, regression coverage and verification boundaries. The academic
PDF/Word report is unchanged; these improvements are reserved for the Task 7 report update.
