"""Task11A presentation contracts; no analytical or ML changes."""
from pathlib import Path
import subprocess
from fastapi.testclient import TestClient
from app.main import app

ROOT=Path(__file__).resolve().parents[1]


def test_cinematic_lifecycle_and_numeric_contracts():
    run=subprocess.run(['node','tests/frontend/cinematic.test.cjs'],cwd=ROOT,capture_output=True,text=True,timeout=15)
    assert run.returncode==0,run.stdout+run.stderr


def test_optional_boot_assets_replay_and_no_server_side_overlay():
    with TestClient(app) as client:
        for path in ['/', '/explore', '/workspace/overview', '/workspace/graph', '/workspace/jordan', '/workspace/time-machine']:
            page=client.get(path)
            assert page.status_code==200
            assert '/static/product/cinematic.js' in page.text
            assert '/static/product/cinematic.css' in page.text
            assert 'data-replay-intro' in page.text
            assert 'class="cinematic-boot"' not in page.text
            assert '/static/brand/relic-dark.svg' in page.text
        for name in ['cinematic.js','cinematic.css']:
            assert client.get('/static/product/'+name).status_code==200


def test_frozen_report_source_validation_rejects_wrong_revision_or_hash():
    import importlib.util
    import json
    import pytest
    spec=importlib.util.spec_from_file_location('cinematic_report_validator',ROOT/'tools/validate_report.py')
    validator=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(validator)
    manifest=json.loads((ROOT/'submission/report_manifest.json').read_text())
    revision='09f6b6df29b6b3e8e81c48c7f8f929a6e638dce5'
    validator.checked_sources(manifest,revision)
    manifest['source_sha256']['app/static/product/overview.js']='0'*64
    with pytest.raises(AssertionError):
        validator.checked_sources(manifest,revision)
    with pytest.raises(AssertionError):
        validator.checked_sources(manifest,'main')
