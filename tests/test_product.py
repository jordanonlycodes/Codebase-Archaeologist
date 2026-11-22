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
        assert 'graph-canvas' not in response.text and '/static/product/workspace.js' not in response.text
        assert "script-src 'self'" in response.headers['content-security-policy']
        assert client.get('/explore').status_code==200
        assert client.get('/static/product/landing.js').status_code==200


def test_workspace_store_regressions():
    import subprocess
    run=subprocess.run(['node','tests/frontend/workspace.test.cjs'],cwd=ROOT,capture_output=True,text=True,timeout=30)
    assert run.returncode==0,run.stdout+run.stderr


import pytest
from html.parser import HTMLParser
import json
import os
import subprocess

PAGES=['overview','risk','structure','graph','architecture','heatmaps','blast-radius']


@pytest.mark.parametrize('page',PAGES)
def test_real_workspace_routes_and_lazy_feature_assets(page):
    from app.routes.dashboard import ASSETS
    with TestClient(app) as client:
        response=client.get('/workspace/'+page)
        assert response.status_code==200
        assert f'data-page="{page}"' in response.text
        assert f'href="/workspace/{page}" aria-current="page"' in response.text
        ids=re.findall(r'\bid="([^"]+)"',response.text)
        assert len(ids)==len(set(ids))
        for source in re.findall(r'(?:src|href)="(/static/[^\"]+)"',response.text):
            assert client.get(source).status_code==200,source
        assert '/static/app.js' not in response.text and '/static/styles.css' not in response.text
        assert '3d-force-graph-1.73.3.min.js' not in response.text
        if page!='graph':assert '/static/graph/three.js' not in response.text
        assert 'no-store' in response.headers['cache-control']
        assert "frame-ancestors 'none'" in response.headers['content-security-policy']
        feature_ids={'graph':'graph-canvas','architecture':'ai-canvas','heatmaps':'ai-canvas','blast-radius':'impact-canvas','risk':'risk-rows','structure':'structure-rows','overview':'file-table-body'}
        assert feature_ids[page] in ids
        for other,id in feature_ids.items():
            if other!=page and id!=feature_ids[page]:assert id not in ids


@pytest.mark.parametrize('route',['/workspace/unknown','/workspace/../missing','/not-a-page'])
def test_invalid_workspace_routes_are_not_fake_dashboards(route):
    with TestClient(app) as client:
        assert client.get(route).status_code==404


class DOM(HTMLParser):
    void={'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}
    def __init__(self):
        super().__init__();self.root={'tag':'document','attrs':{},'children':[]};self.stack=[self.root]
    def handle_starttag(self,tag,attrs):
        item={'tag':tag,'attrs':dict(attrs),'children':[]};self.stack[-1]['children'].append(item)
        if tag not in self.void:self.stack.append(item)
    def handle_endtag(self,tag):
        for index in range(len(self.stack)-1,0,-1):
            if self.stack[index]['tag']==tag:self.stack=self.stack[:index];break
    def handle_data(self,text):
        if text:self.stack[-1]['children'].append(text)


def test_real_documents_boot_with_shared_analysis_and_cross_page_navigation(tmp_path,make_zip):
    with TestClient(app) as client:
        response=client.post('/api/analyze',files={'file':('journey.zip',make_zip({
            'README.md':'Journey fixture\n','app/__init__.py':'','lib/__init__.py':'',
            'app/main.py':'from lib.util import util\ndef entry(x): return util(x)\n',
            'lib/util.py':'def util(x): return x\n',
            'native/main.c':'#include "../include/api.h"\nint caller(int x){return helper(x);}\n',
            'native/util.c':'int helper(int x){return x+1;}\n',
            'include/api.h':'int helper(int x);\n',
        }))})
        assert response.status_code==200,response.text
        python_response=client.post('/api/analyze',files={'file':('python.zip',make_zip({'src/app.py':'def helper(x): return x\ndef entry(x): return helper(x)\n'}))})
        assert python_response.status_code==200,python_response.text
        fixture={'analysis':response.json(),'python_analysis':python_response.json(),'pages':{},'scripts':{}}
        for page in [*PAGES,'explore']:
            html=client.get('/explore' if page=='explore' else '/workspace/'+page).text
            parser=DOM();parser.feed(html);fixture['pages'][page]=parser.root
            fixture['scripts'][page]=re.findall(r'<script src="(/static/[^\"]+)"',html)
        path=tmp_path/'product-fixture.json';path.write_text(json.dumps(fixture))
        run=subprocess.run(['node','tests/frontend/product.test.cjs'],cwd=ROOT,env={**os.environ,'PRODUCT_FIXTURE':str(path)},capture_output=True,text=True,timeout=40)
        assert run.returncode==0,run.stdout+run.stderr
        print(run.stdout)


def test_browser_404_preserves_api_errors_and_recovery_navigation():
    with TestClient(app) as client:
        page=client.get('/workspace/missing',headers={'accept':'text/html'})
        assert page.status_code==404 and 'OUTSIDE THE MAP' in page.text
        assert 'href="/workspace/overview"' in page.text
        api=client.get('/api/missing',headers={'accept':'text/html'})
        assert api.status_code==404 and api.json()['error']['code']=='invalid_request'


def test_readme_brand_svg_is_local_and_github_safe():
    import xml.etree.ElementTree as ET
    hero=ROOT/'docs/assets/hero.svg'
    tree=ET.parse(hero);source=hero.read_text()
    assert tree.getroot().attrib['viewBox']=='0 0 1440 640'
    assert '<script' not in source and '<foreignObject' not in source and '<image' not in source
    assert '<text' not in source  # Font outlines avoid remote font dependencies.
    assert 'not an application screenshot' in source
    readme=(ROOT/'README.md').read_text()
    assert 'docs/assets/hero.svg' in readme
    assert 'Authentic application screenshots are still pending' in readme
    for target in re.findall(r'\]\(([^)]+)\)',readme):
        if '://' not in target and not target.startswith('#'):
            assert (ROOT/target.split('#')[0]).exists(),target


def test_product_csp_does_not_break_existing_fastapi_documentation():
    with TestClient(app) as client:
        assert "script-src 'self'" in client.get('/workspace/overview').headers['content-security-policy']
        docs=client.get('/docs')
        assert docs.status_code==200 and 'swagger-ui-bundle.js' in docs.text
        assert 'content-security-policy' not in docs.headers
        assert client.get('/openapi.json').status_code==200
