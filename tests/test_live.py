"""Presentation route and state contracts; actual instrument acceptance uses Chromium."""
from pathlib import Path
import subprocess
from fastapi.testclient import TestClient
from app.main import app
ROOT=Path(__file__).resolve().parents[1]

def test_live_state_and_evidence_contracts():
    run=subprocess.run(['node','--test','tests/frontend/live.test.cjs'],cwd=ROOT,capture_output=True,text=True,timeout=20)
    assert run.returncode==0,run.stdout+run.stderr

def test_live_route_reuses_instruments_and_safe_external_assets():
    with TestClient(app) as client:
        response=client.get('/live');assert response.status_code==200
        html=response.text
        assert html.count('id="knowledge-explorer"')==1
        assert html.count('id="time-machine"')==1
        assert html.count('data-live-scene=')==6
        assert 'data-intro="off"' in html
        assert 'product/workspace.js' not in html
        for asset in ['product/live.js','product/live.css','graph/xray.js','time_machine/workspace.js']:
            assert client.get('/static/'+asset).status_code==200
        assert 'frame-ancestors' in response.headers['content-security-policy']

def test_live_entry_points_and_native_recovery_controls():
    with TestClient(app) as client:
        for path in ['/','/workspace/overview']:
            assert 'href="/live"' in client.get(path).text
        html=client.get('/live').text
        for control in ['launch','prev','next','exit','fullscreen','record','notes-toggle','restart']:
            assert f'<button id="live-{control}"' in html
        assert '<noscript>' in html and 'This does not create a video' in html
