"""Task 5 assets, page contracts and lifecycle integration."""
from pathlib import Path
import re
from fastapi.testclient import TestClient
from app.main import app

ROOT=Path(__file__).resolve().parents[1]


def test_design_system_assets_and_font_attribution():
    with TestClient(app) as client:
        css=client.get('/static/product/design.css')
        assert css.status_code==200
        assert 'prefers-reduced-motion' in css.text and 'font-display:swap' in css.text
        assert 'https://' not in css.text
        for source in re.findall(r"url\('([^']+)'\)",css.text):
            response=client.get('/static/product/'+source)
            assert response.status_code==200 and len(response.content)>1000
        license=client.get('/static/product/fonts/OFL.txt').text
        assert 'SIL OPEN FONT LICENSE' in license and 'Noto Project Authors' in license


def test_cinematic_landing_and_working_import_entry():
    with TestClient(app) as client:
        response=client.get('/')
        assert response.status_code==200
        assert 'hero-light' in response.text and 'UNCOVER THE UNSEEN' in response.text
        assert 'href="/explore"' in response.text
        assert 'graph-canvas' not in response.text and '/static/app.js' not in response.text
        assert "script-src 'self'" in response.headers['content-security-policy']
        assert client.get('/explore').status_code==200
        assert client.get('/static/product/landing.js').status_code==200
