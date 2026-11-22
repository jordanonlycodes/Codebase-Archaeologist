"""Browser-free frontend checks; real GPU/visual verification remains a manual step."""
import importlib.util
from pathlib import Path
import re
import shutil
import subprocess

import pytest
from fastapi.testclient import TestClient
from app.main import app

ROOT = Path(__file__).resolve().parents[1]


def test_frontend_graph_utilities_and_lifecycle():
    executable = shutil.which('node')
    if executable is None:
        pytest.skip('Node.js is required for graph frontend utility tests (no npm packages needed)')
    result = subprocess.run([executable, 'tests/frontend/graph.test.cjs'], cwd=ROOT,
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr


def test_graph_dashboard_integration_and_static_assets():
    with TestClient(app) as client:
        html = client.get('/').text
        ids = re.findall(r'\bid="([^"]+)"', html)
        assert len(ids) == len(set(ids))
        for required in ['knowledge-explorer', 'graph-2d', 'graph-3d', 'graph-view',
                         'graph-inspection', 'graph-canvas', 'graph-overlay',
                         'graph-hop-1', 'graph-hop-2', 'graph-search-results']:
            assert required in ids
        for filename in ['data.js', 'svg.js', 'three.js', 'explorer.js', 'explorer.css']:
            response = client.get('/static/graph/' + filename)
            assert response.status_code == 200
        assert "script-src 'self'" in client.get('/').headers['content-security-policy']
        assert 'renderKnowledgeGraph(result.knowledge_graph)' in client.get('/static/app.js').text
        for script in ['svg.js', 'three.js', 'explorer.js']:
            source = client.get('/static/graph/' + script).text
            assert '.innerHTML' not in source and 'insertAdjacentHTML' not in source
        assert 'cdn.' not in client.get('/static/graph/three.js').text


def test_graph_controls_have_unique_existing_selectors():
    template = (ROOT/'app/templates/dashboard.html').read_text()
    ids = set(re.findall(r'\bid="([^"]+)"', template))
    source = (ROOT/'app/static/graph/explorer.js').read_text()
    for element_id in re.findall(r"\$\('(graph-[^']+)'\)", source):
        assert element_id in ids, element_id


def test_javascript_syntax():
    executable = shutil.which('node')
    if executable is None:
        pytest.skip('Node.js required for JavaScript syntax verification')
    for source in [* (ROOT/'app/static/graph').glob('*.js'), ROOT/'app/static/app.js']:
        result = subprocess.run([executable, '--check', str(source)], capture_output=True, text=True, timeout=10)
        assert result.returncode == 0, result.stderr


def installer():
    spec = importlib.util.spec_from_file_location('graph_installer', ROOT/'tools/install_graph_assets.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_asset_installer_preserves_pin_license_and_receipt(tmp_path, monkeypatch):
    import io
    import json
    import tarfile
    module = installer()
    archive = io.BytesIO()
    with tarfile.open(fileobj=archive, mode='w:gz') as tar:
        for name, content in {'package.json': json.dumps({'name':'3d-force-graph', 'version':module.VERSION}),
                              'LICENSE':'MIT License fixture', 'dist/3d-force-graph.min.js':'/* test bundle */'}.items():
            data = content.encode()
            member = tarfile.TarInfo('package/' + name)
            member.size = len(data)
            tar.addfile(member, io.BytesIO(data))
    monkeypatch.setattr(module, 'urlopen', lambda *args, **kwargs:io.BytesIO(archive.getvalue()))
    monkeypatch.setattr(module, 'DESTINATION', tmp_path)
    module.install()
    assert (tmp_path/f'3d-force-graph-{module.VERSION}.LICENSE').read_text()=='MIT License fixture'
    receipt = json.loads((tmp_path/'graph-assets.json').read_text())
    assert receipt['version']=='1.73.3' and len(receipt['bundle_sha256'])==64


def test_asset_installer_failure_does_not_create_fake_bundle(tmp_path, monkeypatch):
    module = installer()
    def blocked(*args, **kwargs):
        raise OSError('DNS unavailable')
    monkeypatch.setattr(module, 'urlopen', blocked)
    monkeypatch.setattr(module, 'DESTINATION', tmp_path)
    with pytest.raises(OSError, match='DNS unavailable'):
        module.install()
    assert list(tmp_path.iterdir())==[]
