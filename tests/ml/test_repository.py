"""Inference tests never fit a model or read the dataset/holdout."""
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace
import shutil

import pytest

pytest.importorskip('tree_sitter')
np = pytest.importorskip('numpy')
from app.ml.features import FEATURE_NAMES, extract_features
from app.ml.repository import ModelService, InferenceLimits, analyze_functions
from app.ml.io import read_json, write_json

ARTIFACTS = Path(__file__).resolve().parents[2] / 'artifacts/devign-v1'


class SpyPipeline:
    def predict_proba(self, matrix):
        self.matrix = matrix
        return np.tile([.3, .7], (len(matrix), 1))

    def predict(self, matrix):
        return np.ones(len(matrix), dtype=int)


@pytest.fixture
def service():
    model = ModelService('/unused')
    model.loaded = True
    model.pipeline = SpyPipeline()
    model.metadata = {'model_version': 'test-double-not-trained'}
    return model


def run(tmp_path, service, contents, **kwargs):
    files = []
    for name, source in contents.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source)
        files.append(SimpleNamespace(path=name, bytes=len(source.encode()), is_source=True))
    return analyze_functions(tmp_path, files, service, **kwargs)


def test_multiple_functions_locations_and_shared_features(tmp_path, service):
    first = 'int first(void) { return 1; }'
    result = run(tmp_path, service, {'src/main.c': first + '\n\nint *second(int *p) { return p; }', 'other.cpp': 'int other() {return 0;}', 'main.py': 'x=1'})
    assert result.status == 'ready'
    assert result.analyzed_functions == result.defect_related == 2
    assert result.non_defect_related == result.skipped_functions == 0
    assert result.unsupported_source_files == 2
    assert [(f.name, f.start_line, f.end_line) for f in result.functions] == [('first', 1, 1), ('second', 3, 3)]
    assert all(f.path == 'src/main.c' for f in result.functions)
    assert list(result.functions[0].features) == list(FEATURE_NAMES)
    np.testing.assert_array_equal(service.pipeline.matrix[0], extract_features(first).values)
    assert all(f.model_probability == .7 for f in result.functions)


def test_no_c_does_not_load(tmp_path, service, monkeypatch):
    monkeypatch.setattr(service, 'load', lambda: pytest.fail('Unnecessary model load'))
    assert run(tmp_path, service, {'a.py': 'x=1', 'a.cpp': 'int a() {}'}).status == 'no_functions'


def test_c_without_definitions(tmp_path, service):
    result = run(tmp_path, service, {'a.c': 'int declaration(void); /* int fake() {} */'})
    assert result.status == 'no_functions' and not result.functions


def test_malformed_file_partial_and_valid_function(tmp_path, service):
    result = run(tmp_path, service, {'a.c': 'int good(void) {return 0;}\nint broken( {'})
    assert result.status == 'partial'
    assert result.file_issues
    assert result.functions[0].name == 'good'
    assert result.functions[0].status == 'analyzed'
    assert all(f.model_probability is None for f in result.functions if f.status != 'analyzed')


def test_invalid_function_abstains(tmp_path, service):
    result = run(tmp_path, service, {'a.c': 'int bad(void) { return +; }'})
    assert result.analyzed_functions == 0
    assert result.status == 'partial'


@pytest.mark.parametrize('limits,reason', [
    (InferenceLimits(functions=1), 'function_limit'),
    (InferenceLimits(file_bytes=5), 'source_size_limit'),
    (InferenceLimits(total_bytes=5), 'source_size_limit'),
])
def test_workload_limits(tmp_path, service, limits, reason):
    result = run(tmp_path, service, {'a.c': 'int a(){return 0;} int b(){return 1;}'}, limits=limits)
    assert result.status == 'partial'
    assert any(reason in issue.reason for issue in result.file_issues)
    assert len(result.functions) <= limits.functions


def test_large_function_skipped(tmp_path, service):
    result = run(tmp_path, service, {'a.c': 'int a(){return 0;}'}, limits=InferenceLimits(function_bytes=5))
    assert result.skipped_functions == 1
    assert result.functions[0].status == 'function_size_limit'
    assert result.functions[0].model_probability is None


def test_missing_model_is_cached_and_safe(tmp_path, monkeypatch):
    service = ModelService(tmp_path / 'secret-location')
    calls = []
    def missing(*args, **kwargs):
        calls.append(1)
        raise FileNotFoundError('secret-location password')
    monkeypatch.setattr('app.ml.model_store.load_pipeline', missing)
    for _ in range(2):
        result = run(tmp_path, service, {'a.c': 'int a(){return 0;}'})
        assert result.status == 'unavailable'
        assert 'secret-location' not in str(asdict(result))
    assert len(calls) == 1


@pytest.mark.parametrize('output', ['exception', 'nan', 'range', 'shape'])
def test_invalid_inference_degrades(tmp_path, service, output):
    def broken(matrix):
        if output == 'exception': raise RuntimeError('/private/path')
        return np.array([[.2, float('nan')]]) if output == 'nan' else np.array([[0., 1.5]]) if output == 'range' else np.array([[.5]])
    service.pipeline.predict_proba = broken
    result = run(tmp_path, service, {'a.c': 'int a(){return 0;}'})
    assert result.status == 'partial'
    assert result.skipped_functions == 1
    assert result.functions[0].model_probability is None
    assert '/private' not in str(asdict(result))


@pytest.fixture
def artifacts():
    if not (ARTIFACTS / 'pipeline.joblib').exists():
        pytest.skip('Trusted local model artifacts are absent')
    return ARTIFACTS


def test_real_saved_model_load_predict_and_cache(tmp_path, artifacts, monkeypatch):
    model = ModelService(artifacts)
    pipeline = model.load()
    assert pipeline is not None
    monkeypatch.setattr('app.ml.model_store.load_pipeline', lambda *a, **k: pytest.fail('Model reloaded'))
    assert model.load() is pipeline
    source = 'int example(int x) { if (x > 2) return x; return 0; }'
    result = run(tmp_path, model, {'main.c': source})
    assert result.status == 'ready'
    item = result.functions[0]
    expected = pipeline.predict_proba(np.asarray([extract_features(source).values]))[0, 1]
    assert item.model_probability == expected
    assert 0 <= item.model_probability <= 1


@pytest.mark.parametrize('change', ['ordering', 'checksum', 'environment'])
def test_actual_incompatible_artifacts_unavailable(tmp_path, artifacts, change):
    directory = tmp_path / 'model'
    directory.mkdir()
    for name in ['pipeline.joblib', 'feature_schema.json', 'metadata.json']:
        shutil.copyfile(artifacts / name, directory / name)
    metadata = read_json(directory / 'metadata.json')
    if change == 'ordering': metadata['feature_names'].reverse()
    if change == 'checksum': metadata['pipeline_sha256'] = '0' * 64
    if change == 'environment': metadata['environment']['scikit-learn'] = '0'
    write_json(directory / 'metadata.json', metadata)
    assert ModelService(directory).load() is None


def test_api_real_zip_and_export_contract(artifacts, monkeypatch, make_zip):
    from fastapi.testclient import TestClient
    from app.main import app
    monkeypatch.setattr('app.ml.repository.SERVICE', ModelService(artifacts))
    with TestClient(app) as client:
        response = client.post('/api/analyze', files={'file': ('mixed.zip', make_zip({'src/real.c': 'int real(void) {return 0;}\nint next(int x) {return x+1;}', 'main.py': 'x = 1', 'code.cpp': 'int cpp() {return 1;}'}))})
        assert response.status_code == 200, response.text
        data = response.json()
        assert data['summary']['files'] == 3
        assert data['defect_risk']['analyzed_functions'] == 2
        assert {f['path'] for f in data['defect_risk']['functions']} == {'src/real.c'}
        assert all(0 <= f['model_probability'] <= 1 for f in data['defect_risk']['functions'])
        assert '/tmp/' not in response.text
        schema = client.get('/openapi.json').json()
        assert 'defect_risk' in schema['components']['schemas']['AnalysisResult']['properties']
        html = client.get('/explore').text
        assert 'Defect Risk Intelligence' in html and 'risk-detail' in html
        script = client.get('/static/app.js').text
        assert 'JSON.stringify(result, null, 2)' in script  # Export includes entire API response.
        assert 'renderDefectRisk(result.defect_risk)' in script
        assert client.get('/static/risk.js').status_code == 200


def test_api_missing_model_keeps_static_results(tmp_path, monkeypatch, make_zip):
    from fastapi.testclient import TestClient
    from app.main import app
    monkeypatch.setattr('app.ml.repository.SERVICE', ModelService(tmp_path / 'missing'))
    with TestClient(app) as client:
        response = client.post('/api/analyze', files={'file': ('source.zip', make_zip({'a.c': 'int a(){return 0;}'}))})
        assert response.status_code == 200
        assert response.json()['summary']['files'] == 1
        assert response.json()['defect_risk']['status'] == 'unavailable'
