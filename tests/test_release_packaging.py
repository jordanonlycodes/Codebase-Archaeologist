"""Release artifact integrity without benchmark fitting or dependency downloads."""
from pathlib import Path
import importlib.util,json,shutil
import pytest
ROOT=Path(__file__).resolve().parents[1]
def module(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/'tools'/f'{name}.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def test_approved_model_installs_without_dataset_and_is_idempotent(tmp_path):
    m=module('install_model');target=tmp_path/'installed'
    first=m.install(destination=target);second=m.install(destination=target)
    assert first==second and first['sha256']==m.APPROVED
    assert sorted(p.name for p in target.iterdir())==sorted(m.NAMES)


def test_corrupt_model_is_rejected_before_any_destination_write(tmp_path):
    m=module('install_model');source=tmp_path/'source';shutil.copytree(ROOT/'models/devign-v1',source)
    (source/'pipeline.joblib').write_bytes(b'not a pickle');target=tmp_path/'installed'
    with pytest.raises(ValueError,match='integrity'):m.install(source,target)
    assert not target.exists()


def test_installer_preserves_different_existing_model(tmp_path):
    m=module('install_model');target=tmp_path/'installed';target.mkdir();(target/'pipeline.joblib').write_bytes(b'preserve me')
    with pytest.raises(ValueError,match='overwrite'):m.install(destination=target)
    assert (target/'pipeline.joblib').read_bytes()==b'preserve me'


def test_release_model_metadata_matches_original_evidence():
    source=ROOT/'models/devign-v1';meta=json.loads((source/'metadata.json').read_text())
    assert meta==json.loads((ROOT/'reports/ml/model_metadata.json').read_text())
    assert meta['threshold']==.5 and len(meta['feature_names'])==11
    assert meta['model_version']=='devign-v1-4a23cc304ca8'


def test_portable_demo_archive_is_deterministic_and_original():
    import io,zipfile
    m=module('release_smoke');data=m.demo_bytes();assert data==m.demo_bytes()
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        assert sorted(z.namelist())==['helpers.py','review.c']
        assert z.testzip() is None


def test_source_archive_policy_excludes_private_cache_and_unapproved_vendor():
    m=module('build_submission')
    for name in ['.git/config','.venv/lib/file','data/a.parquet','artifacts/model.joblib','.env','secrets/key','app/static/vendor/3d-force-graph-1.73.3.min.js','submission/final/payload/a','../outside','/absolute','models/other.joblib']:
        assert not m.source_allowed(name),name
    assert m.source_allowed('models/devign-v1/pipeline.joblib') and m.source_allowed('app/main.py')


def test_archives_reject_unsafe_or_duplicate_names(tmp_path):
    m=module('build_submission')
    with pytest.raises(ValueError):m.write_zip(tmp_path/'unsafe.zip',[('../x',b'bad')])
    with pytest.raises(ValueError):m.write_zip(tmp_path/'duplicate.zip',[('x',b'a'),('x',b'b')])
    assert not (tmp_path/'unsafe.zip').exists()


def test_archive_inventory_detects_tampering_and_preserves_reproducibility(tmp_path):
    import zipfile
    m=module('build_submission');folder=tmp_path/'payload';folder.mkdir();(folder/'a').write_bytes(b'actual')
    records=m.inventory(folder);m.verify_inventory(folder,records)
    m.write_zip(tmp_path/'one.zip',[('a',b'actual')]);m.write_zip(tmp_path/'two.zip',[('a',b'actual')])
    assert (tmp_path/'one.zip').read_bytes()==(tmp_path/'two.zip').read_bytes()
    with zipfile.ZipFile(tmp_path/'one.zip') as z:assert z.read('a')==b'actual' and z.testzip() is None
    (folder/'a').write_bytes(b'changed')
    with pytest.raises(ValueError):m.verify_inventory(folder,records)


def test_vendor_status_never_claims_unverified_redistribution(tmp_path):
    m=module('verify_vendor_assets');result=m.inspect(tmp_path)
    assert result['local_bundle_available'] is False and result['redistribution_approved'] is False


def test_academic_details_are_explicit_and_exact():
    d=json.loads((ROOT/'submission/academic_details.json').read_text())
    assert d['institution']=='FAST NUCES Peshawar' and d['department']=='SE'
    assert d['course']=='AI-lab' and d['instructor']=='M. Saad Khan'
    assert d['semester']=='5' and d['submission_date']=='23 November, 2026'
    assert d['authors']==[{'name':'Bilal Malik','roll':'24P-3061'},{'name':'Aun Anis','roll':'24P-3017'}]
