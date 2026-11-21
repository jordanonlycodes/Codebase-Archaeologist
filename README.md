# Codebase Archaeologist

A local repository intelligence dashboard built with FastAPI, Jinja2, vanilla JavaScript and custom CSS. Upload a repository ZIP to inspect real file, language and line metrics. Uploaded code is **never executed**.

This is the Task 1 foundation. No model is trained or bundled, no vulnerability score is fabricated, and GitHub URL ingestion is not implemented or presented as available.

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

Package installation requires access to PyPI. This project needs no database, credentials, Node build, containers or ML packages. Dashboard assets are local; the optional Swagger API documentation uses FastAPI's default CDN assets.

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
│   │   └── inference.py        # Future RiskModel protocol
│   ├── templates/dashboard.html
│   └── static/{app.js,styles.css,mark.svg}
├── tests/
│   ├── conftest.py
│   ├── test_archive.py
│   ├── test_scanner.py
│   ├── test_api.py
│   └── test_middleware.py
├── .gitignore
├── pytest.ini
├── requirements.txt
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

## Future ML integration

`app/ml/inference.py` defines `RiskModel.predict(analysis: AnalysisResult) -> RiskPrediction` and `UnavailableModel`, which raises `NotImplementedError`. `app/analysis/models.py` supplies the typed, versioned deterministic input. Future feature engineering and model providers can use this seam without mixing inference with ZIP ingestion or routing.

There is no model loading, training, inference endpoint or displayed prediction in this phase. Training data, calibration, evaluation and model lifecycle work are deliberately deferred.
