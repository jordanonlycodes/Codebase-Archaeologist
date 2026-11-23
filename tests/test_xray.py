"""Source-grounded X-Ray presentation and deterministic hierarchy contracts."""
from pathlib import Path
import subprocess
from fastapi.testclient import TestClient
from app.main import app

ROOT=Path(__file__).resolve().parents[1]


def test_xray_hierarchy_trace_risk_and_navigation_contracts():
    run=subprocess.run(['node','--test','tests/frontend/xray.test.cjs'],cwd=ROOT,capture_output=True,text=True,timeout=20)
    assert run.returncode==0,run.stdout+run.stderr


def test_xray_assets_semantic_controls_and_progressive_fallback():
    with TestClient(app) as client:
        html=client.get('/workspace/graph').text
        assert html.index('/static/graph/explorer.js')<html.index('/static/graph/xray.js')<html.index('/static/product/workspace.js')
        assert 'id="xray-workspace"' in html and 'Activate X-Ray' in html
        for control in ['activate','exit','back','forward','root','clear','universe']:
            assert f'<button id="xray-{control}"' in html
        assert 'aria-label="Investigation breadcrumbs"' in html
        for asset in ['/static/graph/xray.js','/static/graph/xray.css']:
            assert client.get(asset).status_code==200
        js=client.get('/static/graph/xray.js').text
        assert 'fetch(' not in js and '.innerHTML' not in js
        assert 'var(--radius-lg)' in client.get('/static/graph/xray.css').text


def test_xray_is_lazy_and_does_not_affect_other_workspaces():
    with TestClient(app) as client:
        for page in ['overview','architecture','heatmaps','jordan','time-machine']:
            assert '/static/graph/xray.js' not in client.get('/workspace/'+page).text
