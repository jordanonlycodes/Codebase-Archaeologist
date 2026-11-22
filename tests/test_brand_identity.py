"""Local brand asset and shell contracts; no claim of browser visual acceptance."""
from pathlib import Path
from xml.etree import ElementTree as ET
import re

from fastapi.testclient import TestClient
from app.main import app

ROOT = Path(__file__).resolve().parents[1]


def test_relic_assets_are_local_accessible_vectors_without_active_content():
    assets = sorted((ROOT/'app/static/brand').glob('*.svg'))
    assert len(assets) == 7
    with TestClient(app) as client:
        for asset in assets:
            xml = ET.fromstring(asset.read_text())
            assert xml.tag == '{http://www.w3.org/2000/svg}svg'
            assert xml.find('{http://www.w3.org/2000/svg}title').text
            assert xml.attrib['viewBox'] and xml.attrib['width'] and xml.attrib['height']
            for element in xml.iter():
                assert element.tag.split('}')[-1] not in {'script','foreignObject','image','use'}
                assert not any(key.startswith('on') or key.endswith('href') for key in element.attrib)
            response = client.get('/static/brand/'+asset.name)
            assert response.status_code == 200
            assert response.headers['content-type'].startswith('image/svg+xml')
        png = client.get('/static/brand/apple-touch-icon.png')
        assert png.status_code == 200 and png.content.startswith(b'\x89PNG\r\n\x1a\n')
        assert client.get('/static/mark.svg').status_code == 200


def test_brand_assets_integrated_in_public_and_workspace_shells():
    with TestClient(app) as client:
        for route in ['/', '/explore', '/workspace/overview', '/workspace/graph', '/workspace/jordan']:
            html = client.get(route).text
            assert 'href="/static/brand/favicon.svg"' in html
            assert 'rel="apple-touch-icon"' in html
            assert 'src="/static/brand/relic-dark.svg" width="32" height="35"' in html
            for url in re.findall(r'(?:href|src)="(/static/brand/[^"]+)"', html):
                assert client.get(url).status_code == 200
        readme=(ROOT/'README.md').read_text()
        assert 'Bilal Malik · 24P-3061' in readme and 'Aun Anis · 24P-3017' in readme
        assert 'Individual project with instructor-approved solo participation' not in readme
