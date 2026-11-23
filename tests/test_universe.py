"""Repository Universe presentation, offline assets and shared control contracts."""
from pathlib import Path
import subprocess
from fastapi.testclient import TestClient
from app.main import app

ROOT=Path(__file__).resolve().parents[1]


def test_universe_data_camera_and_tour_contracts():
    result=subprocess.run(['node','--test','tests/frontend/universe.test.cjs'],cwd=ROOT,capture_output=True,text=True,timeout=20)
    assert result.returncode==0,result.stdout+result.stderr


def test_universe_assets_remain_local_and_controls_are_semantic():
    with TestClient(app) as client:
        html=client.get('/workspace/graph').text
        assert html.index('/static/graph/universe.js')<html.index('/static/graph/three.js')
        for name in ['universe-start','universe-pause','universe-next','universe-exit','universe-frame','universe-cluster','universe-tour-status']:
            assert f'id="{name}"' in html
        assert 'Reset Universe' in html and '3D Universe' in html
        js=client.get('/static/graph/universe.js')
        assert js.status_code==200 and 'fetch(' not in js.text and '.innerHTML' not in js.text


def test_shared_controls_load_after_feature_styles_on_every_route():
    with TestClient(app) as client:
        for page in ['/', '/explore', *['/workspace/'+p for p in ['overview','risk','structure','graph','architecture','heatmaps','blast-radius','jordan','time-machine']]]:
            html=client.get(page).text
            assert '/static/product/controls.css' in html
            assert html.index('/static/product/controls.css')>html.index('/static/product/design.css')
            if '/static/graph/explorer.css' in html:
                assert html.index('/static/product/controls.css')>html.index('/static/graph/explorer.css')
        css=client.get('/static/product/controls.css').text
        for token in ['--radius-xs:6px','--radius-sm:9px','--radius-md:12px','--radius-lg:16px','--radius-xl:20px','--radius-pill:999px']:
            assert token in css
        assert ':focus-visible' in css and 'prefers-reduced-motion' in css
        assert 'svg{' not in css and 'canvas{' not in css
