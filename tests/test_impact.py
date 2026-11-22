"""Exercise the same browser/Node query engine against real ingestion results."""
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import zipfile

import pytest
from fastapi.testclient import TestClient
from app.main import app

ROOT=Path(__file__).resolve().parents[1]


def node():
    executable=shutil.which('node')
    if not executable:
        pytest.skip('Node.js required for the shared impact query engine')
    return executable


def test_impact_engine_controller_and_syntax():
    run=subprocess.run([node(),'tests/frontend/impact.test.cjs'],cwd=ROOT,capture_output=True,text=True,timeout=30)
    assert run.returncode==0,run.stdout+run.stderr
    for source in (ROOT/'app/static/impact').glob('*.js'):
        run=subprocess.run([node(),'--check',str(source)],capture_output=True,text=True,timeout=10)
        assert run.returncode==0,run.stderr


def test_dashboard_handoffs_and_safe_assets():
    with TestClient(app) as client:
        page=client.get('/workspace/blast-radius').text
        ids=re.findall(r'\bid="([^"]+)"',page)
        assert len(ids)==len(set(ids))
        for name in ['engine.js','explorer.js','explorer.css']:
            response=client.get('/static/impact/'+name)
            assert response.status_code==200
            assert '.innerHTML' not in response.text and 'insertAdjacentHTML' not in response.text
            assert 'fetch(' not in response.text
        script=client.get('/static/impact/explorer.js').text
        for identity in re.findall(r"\$\('(impact-[^']+)'\)",script):
            assert identity in ids,identity
        app_script=client.get('/static/product/workspace.js').text
        assert 'renderImpact(result.knowledge_graph, result.architecture, result.structural)' in app_script
        assert 'result.blast_radius=query' in app_script
        assert 'root.impactExplorer?.open(n.id)' in client.get('/static/graph/explorer.js').text
        assert 'root.impactExplorer?.open(impactId)' in client.get('/static/architecture/explorer.js').text


@pytest.mark.parametrize('missing_model',[False,True])
def test_real_mixed_zip_and_existing_json_contract(tmp_path,monkeypatch,missing_model):
    if missing_model:
        from app.ml.repository import ModelService
        monkeypatch.setattr('app.ml.repository.SERVICE',ModelService(tmp_path/'unavailable-model'))
    archive=io.BytesIO()
    with zipfile.ZipFile(archive,'w') as stream:
        for name,source in {
            'README.md':'Mixed impact fixture\n','app/__init__.py':'','lib/__init__.py':'',
            'app/main.py':'from lib.util import pyhelper\ndef entry(x): return pyhelper(x)\n',
            'lib/util.py':'def pyhelper(x): return x\n',
            'native/main.c':'#include "../include/api.h"\nint run(int x){return helper(x);}\n',
            'native/util.c':'int helper(int x){return x+1;}\n',
            'include/api.h':'int helper(int x);\n',
        }.items():
            stream.writestr(name,source)
    with TestClient(app) as client:
        response=client.post('/api/analyze',files={'file':('mixed.zip',archive.getvalue(),'application/zip')})
    assert response.status_code==200,response.text
    data=response.json()
    for field in ['files','summary','structural','defect_risk','knowledge_graph','architecture','source']:
        assert field in data
    # Impact is a query over this snapshot, not a misleading precomputed all-repository prediction.
    assert 'blast_radius' not in data
    artifact=tmp_path/'analysis.json'
    artifact.write_text(json.dumps(data))
    environment={**os.environ,'IMPACT_SMOKE_JSON':str(artifact)}
    run=subprocess.run([node(),'tests/frontend/impact.test.cjs'],cwd=ROOT,env=environment,capture_output=True,text=True,timeout=30)
    assert run.returncode==0,run.stdout+run.stderr
    print(next(line for line in run.stdout.splitlines() if 'SMOKE' in line))
