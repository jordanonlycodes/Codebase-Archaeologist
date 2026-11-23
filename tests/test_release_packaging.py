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
