"""Offline release evidence checks; genuine browser captures are produced separately."""
from pathlib import Path
import hashlib,importlib.util,json,struct,zipfile
ROOT=Path(__file__).resolve().parents[1]
def load(name):
 spec=importlib.util.spec_from_file_location(name,ROOT/'tools'/f'{name}.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def test_reviewed_graph_bytes_and_closed_notice_inventory():
 assert load('verify_vendor_assets').inspect()['redistribution_approved']
 p=json.loads((ROOT/'third_party/graph/provenance.json').read_text())
 assert len(p['packages'])==35
 assert {x['license'] for x in p['packages']}=={'MIT','ISC','BSD-3-Clause'}
 notice=(ROOT/'third_party/graph/LICENSES.txt').read_text()
 assert all(x['package']+'@'+x['version'] in notice for x in p['packages'])
 assert hashlib.sha256((ROOT/'third_party/graph/upstream-yarn.lock').read_bytes()).hexdigest()==p['source_lock_sha256']

def test_tampered_vendor_bundle_cannot_be_approved(tmp_path):
 import shutil
 for name in ['graph-assets.json','3d-force-graph-1.73.3.LICENSE']:
  shutil.copyfile(ROOT/'app/static/vendor'/name,tmp_path/name)
 (tmp_path/'3d-force-graph-1.73.3.min.js').write_bytes(b'corrupt')
 assert not load('verify_vendor_assets').inspect(tmp_path)['redistribution_approved']

def test_packaging_requires_reviewed_exact_vendor_allowlist():
 m=load('build_submission')
 assert not m.source_allowed('app/static/vendor/arbitrary.js')
 assert not m.reviewed_graph_allowed('app/static/vendor/arbitrary.js')
 assert all(m.reviewed_graph_allowed(n) for n in m.GRAPH_FILES)

def test_genuine_registered_screenshots_match_embedded_docx_images():
 shots=json.loads((ROOT/'submission/screenshots.json').read_text())
 assert len(shots)==3
 with zipfile.ZipFile(ROOT/'submission/Codebase_Archaeologist_Report.docx') as z:
  embedded={hashlib.sha256(z.read(n)).hexdigest() for n in z.namelist() if n.startswith('word/media/')}
 for shot in shots:
  p=ROOT/shot['path'];data=p.read_bytes()
  assert shot['verified'] and data[:8]==b'\x89PNG\r\n\x1a\n'
  width,height=struct.unpack('>II',data[16:24]);assert width>=1000 and height>=768
  assert hashlib.sha256(data).hexdigest()==shot['sha256'] and shot['sha256'] in embedded
  assert all(shot.get(k) for k in ['captured_at','repository','revision_or_fixture','browser','viewport','captured_by'])

def test_browser_evidence_has_no_failed_measured_cases():
 r=json.loads((ROOT/'reports/release/task7e/browser.json').read_text())
 assert r['browser']=='Chromium157.0.8103.79' and r['live_history']['source']['snapshot_commit']=='7fd1a60b01f91b314f59955a4e4d4e80d8edf11d'
 assert len(r['checks'])>=40 and all(x['pass'] for x in r['checks'])
 assert {x['width'] for x in r['checks'] if x['name']=='responsive'}=={1440,1024,768,390}
 assert r['claims']['physical_gpu_fps_measured'] is False

def test_final_promotion_rejects_unaccepted_source_revision():
 import pytest
 with pytest.raises((ValueError,FileNotFoundError)):
  load('build_submission').require_final_acceptance('0'*40)


def test_report_figure_listing_includes_continuation_tables():
 import xml.etree.ElementTree as ET
 m=load('validate_report')
 with zipfile.ZipFile(ROOT/'submission/Codebase_Archaeologist_Report.docx') as z:
  children=list(ET.fromstring(z.read('word/document.xml')).find('w:body',m.NS))
 rows=m.listing_rows(children,'List of Figures')
 assert len(rows)==14
 labels=[''.join(t.text or '' for t in row.find('w:tc',m.NS).findall('.//w:t',m.NS)) for row in rows]
 assert all(label.startswith(f'Figure {i}.') for i,label in enumerate(labels,1))
