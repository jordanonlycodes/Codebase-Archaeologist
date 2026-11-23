# Task 7C — authentic screenshot capture and regeneration

No current authentic application screenshots are present. Fresh Chromium on23 November
exited signal5 before rendering (`setsockopt: Operation not permitted`); no fake captures
are supplied. The report contains three literal SCREENSHOT NOT YET CAPTURED paragraphs,
not synthetic dashboard images. Scientific plots/architecture diagrams are not UI captures.

## Local capture procedure (Ubuntu / actual application)

From repository root, activate the existing environment and trusted model prerequisites:

```bash
source .venv/bin/activate
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

For a fresh machine first follow README.md and docs/ml_pipeline.md. Do not load downloaded
untrusted joblib files. No cloud key is needed. Open http://127.0.0.1:8000 at1366×768;
record actual browser/version, OS, viewport and date. Create a shareable ZIP:

```bash
python - <<'PY'
from pathlib import Path
from zipfile import ZipFile
with ZipFile('/tmp/university-demo.zip','w') as archive:
    for source in sorted(Path('tests/fixtures/university_demo').glob('*')):
        if source.is_file(): archive.write(source, source.name)
PY
```

1. Import the ZIP at /explore. Confirm genuine C-only scores and unscored Python structure.
2. Save docs/screenshots/overview.png from /workspace/overview after results settle.
3. Capture graph-3d.png only if real WebGL is available. Select an actual entity with
   evidence. Test rotate, zoom, explicit Pan camera, resize and Reset View. Do not name a
   2D fallback image graph-3d or imply missing vendor assets loaded successfully.
4. Also capture risk, structure, graph2D, architecture, heatmaps, Blast Radius path and
   Jordan Local where useful. Do not include private code/paths or hide coverage warnings.
5. A source ZIP must show no history. For time-machine.png import a small public GitHub
   repository, record the exact source.snapshot_commit, wait for actual bounded history,
   then capture timeline/activity or a real comparison. Respect quota/errors; never use
   mocked HTTP fixtures as screenshots of a live public repository.
6. Inspect each image at full resolution: labels readable, no clipped toolbar or personal
   information. Test390px width and reduced motion separately; a desktop still is not proof
   of mobile/accessibility/animation performance. Record pass/fail locally.

## Register provenance and rebuild

Edit submission/screenshots.json. Set verified:true only after human inspection, and add
all fields:captured_at,repository,revision_or_fixture,browser,viewport,captured_by. Keep
path repository-relative and caption factual. Do not create a mock file to satisfy checks.
The three registered entries populate the report; additional genuine entries can be added.

```bash
.venv/bin/python tools/generate_report.py
.venv/bin/python tools/validate_report.py
.venv/bin/python tools/check_report_links.py
```

Generation embeds verified images/captions with provenance and otherwise preserves the
explicit placeholders. Review new pagination/lists and render the PDF again. Open DOCX
in Word/LibreOffice, check tables/figures/page fields, and locally export PDF if identical
Office pagination is required. Version both regenerated documents and manifests together.
