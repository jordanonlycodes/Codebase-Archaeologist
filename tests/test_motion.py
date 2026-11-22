"""Finite motion contracts; native browser rendering is a separate acceptance check."""
from pathlib import Path
import subprocess
from fastapi.testclient import TestClient
from app.main import app

ROOT = Path(__file__).resolve().parents[1]


def test_motion_lifecycle_reduced_preference_and_factual_counters():
    result = subprocess.run(['node', 'tests/frontend/motion.test.cjs'], cwd=ROOT,
                            capture_output=True, text=True, timeout=15)
    assert result.returncode == 0, result.stdout + result.stderr


def test_motion_assets_are_local_and_progressive():
    with TestClient(app) as client:
        js = client.get('/static/product/motion.js')
        css = client.get('/static/product/motion.css')
        assert js.status_code == css.status_code == 200
        assert 'prefers-reduced-motion' in js.text and 'prefers-reduced-motion' in css.text
        assert '.innerHTML' not in js.text and 'fetch(' not in js.text
        assert 'fill:\'none\'' in js.text
        assert 'opacity:0' not in css.text  # No stylesheet hides initial essential content.


def test_workspace_motion_load_order_and_brand_preservation():
    with TestClient(app) as client:
        for page in ['overview','graph','architecture','heatmaps','blast-radius','jordan','time-machine']:
            html=client.get('/workspace/'+page).text
            assert html.index('/static/product/motion.js') < html.index('/static/product/workspace.js')
            assert '/static/product/motion.css' in html
            assert '/static/brand/relic-dark.svg' in html
        assert '/static/product/motion.js' not in client.get('/').text
