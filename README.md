# Codebase Archaeologist

A local repository intelligence dashboard built with FastAPI, Jinja2, vanilla JavaScript and custom CSS. Upload a repository ZIP to inspect real file, language and line metrics. Uploaded code is **never executed**.

Task 1 provides the repository dashboard. Task 2 adds an optional, reproducible C-function research pipeline using the official CodeXGLUE/Devign splits. A Random Forest was trained locally and evaluated once on the official test holdout. Model predictions are **not integrated into the dashboard**. GitHub URL ingestion remains unavailable.

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

Package installation requires access to PyPI. The dashboard needs no database, credentials, Node build, containers or ML packages. Dashboard assets are local; the optional Swagger API documentation uses FastAPI's default CDN assets. The optional training dependencies and commands are documented below.

## Run

From the project directory:

```bash
source .venv/bin/activate
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Open **http://127.0.0.1:8000**. Select or drop a ZIP; analysis starts immediately. Progress reflects bytes uploaded, followed by an indeterminate validation/scanning state. Results include searchable, sortable, paginated files and a JSON download. New failures retain the previous successful analysis with an explicit notice.

Use this as a local, single-user application. Two analyses per process may run concurrently; additional requests receive `429`. Normal completion and handled failures remove uploaded/extracted temporary files. A process crash or forced termination may leave OS temporary files; normal OS temporary-directory cleanup still applies. Results are held in browser memory, not persisted.

## API

- `GET /` — dashboard.
- `GET /api/health` — health response.
- `POST /api/analyze` — one multipart file named `file`, containing a `.zip` archive.
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

## Task 3 integration seam

`app/ml/inference.py` preserves `RiskModel`, `RiskPrediction` and `UnavailableModel`, and adds `FunctionRiskModel.predict_function(source)`. `LocalCFunctionModel` in `app/ml/c_model.py` explicitly loads a trusted local artifact, checks schema/version/checksum compatibility and uses the same feature extractor. It abstains on missing, malformed or unparseable C input. Joblib files can execute code during loading; uploaded repositories must never supply model artifacts.

The repository-level `predict(AnalysisResult)` remains unavailable because aggregate repository totals cannot supply C-function features. Task 3 needs function extraction with source locations, explicit model loading, abstention reporting and a justified aggregation policy. Calibration and independent-project evaluation remain necessary before production use. No FastAPI route or dashboard invokes a model in Task 2.
