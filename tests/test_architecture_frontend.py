"""Test adapter contracts and integration, without claiming visual browser verification."""
from pathlib import Path
import re
import shutil
import subprocess

import pytest
from fastapi.testclient import TestClient
from app.main import app

ROOT=Path(__file__).resolve().parents[1]


def test_architecture_frontend_suite_and_syntax():
    node=shutil.which('node')
    if not node: pytest.skip('Node.js required for browser-free frontend verification')
    result=subprocess.run([node,'tests/frontend/architecture.test.cjs'],cwd=ROOT,capture_output=True,text=True,timeout=30)
    assert result.returncode==0,result.stdout+result.stderr
    for file in (ROOT/'app/static/architecture').glob('*.js'):
        result=subprocess.run([node,'--check',str(file)],capture_output=True,text=True,timeout=10)
        assert result.returncode==0,result.stderr


def test_architecture_dashboard_contract_and_source_safety():
    with TestClient(app) as client:
        response=client.get('/')
        ids=re.findall(r'\bid="([^"]+)"',response.text)
        assert len(ids)==len(set(ids))
        for id in ['architecture-intelligence','ai-architecture','ai-heatmap','ai-metric','ai-area','ai-inspector','ai-canvas','ai-breadcrumbs','ai-focus']:
            assert id in ids
        for name in ['data.js','scene.js','explorer.js','explorer.css']:
            response=client.get('/static/architecture/'+name)
            assert response.status_code==200
            assert '.innerHTML' not in response.text and 'insertAdjacentHTML' not in response.text
        script=client.get('/static/architecture/explorer.js').text
        assert 'XMLHttpRequest' not in script and 'fetch(' not in script
        assert 'renderArchitecture(result.architecture, result.knowledge_graph, result.structural)' in client.get('/static/app.js').text
        for id in re.findall(r"\$\('(ai-[^']+)'\)",script):
            assert id in ids,id
