"""Academic document invariants; saved evidence only, never fit/evaluate a model."""
import importlib.util,json,subprocess,sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('report_validator',ROOT/'tools/validate_report.py')
validator=importlib.util.module_from_spec(spec);spec.loader.exec_module(validator)


def test_current_report_documents_pass_actual_validator():
    result=subprocess.run([sys.executable,'tools/validate_report.py'],cwd=ROOT,capture_output=True,text=True,timeout=45)
    assert result.returncode==0,result.stdout+result.stderr
    evidence=json.loads(result.stdout)
    assert evidence['chapters']==17 and evidence['appendices']==5
    assert evidence['two_author_metadata_and_identity_valid']
    assert evidence['verified_application_screenshots']==json.loads((ROOT/'submission/report_manifest.json').read_text())['screenshots_verified']
    assert evidence['pdf_text_outside_page']==[]


def test_manifest_rejects_deleted_source_instead_of_silently_refreshing_hash():
    manifest=json.loads((ROOT/'submission/report_manifest.json').read_text())
    manifest['source_sha256']['app/templates/dashboard.html']='0'*64
    with pytest.raises(AssertionError):validator.checked_sources(manifest)


def test_manifest_rejects_changed_current_source():
    manifest=json.loads((ROOT/'submission/report_manifest.json').read_text())
    manifest['source_sha256']['app/routes/analysis.py']='0'*64
    with pytest.raises(AssertionError):validator.checked_sources(manifest)


def test_report_sources_preserve_model_and_screenshot_boundary():
    text=(ROOT/'tools/report_content.py').read_text()
    assert 'No new test predictions' in text and 'always-positive' in text
    assert 'not deployed' in text and 'SCREENSHOT NOT YET CAPTURED' in text
    assert 'joblib.load' not in text and '.fit(' not in text
    assert '24P-3061' in text and '24P-3017' in text
