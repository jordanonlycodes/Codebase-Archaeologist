"""Academic evidence invariants; no training or held-out prediction pass."""
import json
from pathlib import Path
import pytest
from app.ml.features import FEATURE_NAMES,FEATURE_VERSION

ROOT=Path(__file__).resolve().parents[1]


def read(name):return json.loads((ROOT/'reports/ml'/name).read_text())


def test_saved_confusion_counts_support_reported_metrics_and_split_labels():
    comparison=read('model_comparison.json');test=read('test_evaluation.json')
    assert set(comparison)=={'logistic_regression','random_forest','hist_gradient_boosting'}
    groups=[m[s] for m in comparison.values() for s in ['train','validation']]+[test['metrics']]
    for row in groups:
        (tn,fp),(fn,tp)=row['confusion_matrix'];assert tn+fp+fn+tp==row['rows']
        assert row['class_counts']=={'0':tn+fp,'1':tp+fn}
        assert row['accuracy']==pytest.approx((tp+tn)/row['rows'])
        assert row['precision']==pytest.approx(tp/(tp+fp))
        assert row['recall']==pytest.approx(tp/(tp+fn))
        assert row['f1']==pytest.approx(2*tp/(2*tp+fp+fn))
        # ROC-AUC requires score ranks and cannot be reconstructed from this matrix.
        assert 0<=row['roc_auc']<=1 and row['threshold']==.5
    assert max(comparison,key=lambda name:comparison[name]['validation']['f1'])=='random_forest'
    assert test['evaluations']==1 and test['selected_before_test'] is True
    assert test['integrity']['used_for_model_selection'] is False


def test_saved_feature_schema_cleaning_and_model_metadata_agree():
    schema=read('feature_schema.json');meta=read('model_metadata.json');clean=read('cleaning_audit.json')
    assert schema['names']==meta['feature_names']==list(FEATURE_NAMES)
    assert schema['version']==meta['feature_version']==FEATURE_VERSION
    assert set(schema['excluded_inputs'])=={'target','project','commit_id','id'}
    assert len(FEATURE_NAMES)==11 and schema['dtype']=='float64'
    assert meta['threshold']==.5
    assert meta['selection']['model']=='random_forest' and meta['selection']['test_used'] is False
    assert clean['test_labels_used'] is False and clean['test_rows_modified']==0
    assert all(item['function_groups']==0 for item in clean['overlap_after'].values())


def test_original_demo_zip_uses_real_trusted_pipeline_and_c_only_features(monkeypatch):
    import io,zipfile
    import numpy as np
    from fastapi.testclient import TestClient
    from app.main import app
    from app.ml.repository import ModelService
    artifact=ROOT/'artifacts/devign-v1'
    if not (artifact/'pipeline.joblib').exists():pytest.skip('Trusted local artifact required for genuine inference demo')
    service=ModelService(artifact);pipeline=service.load();assert pipeline is not None
    monkeypatch.setattr('app.ml.repository.SERVICE',service)
    stream=io.BytesIO();fixture=ROOT/'tests/fixtures/university_demo'
    with zipfile.ZipFile(stream,'w') as archive:
        for name in ['review.c','helpers.py']:archive.write(fixture/name,name)
    with TestClient(app) as client:
        response=client.post('/api/analyze',files={'file':('university-demo.zip',stream.getvalue())})
        assert response.status_code==200,response.text
        data=response.json();risk=data['defect_risk']
        assert data['summary']['files']==2 and risk['analyzed_functions']==3
        assert {f['name'] for f in risk['functions']}=={'clamp_index','sum_values','entry'}
        assert all(f['path']=='review.c' and f['status']=='analyzed' for f in risk['functions'])
        for f in risk['functions']:
            assert list(f['features'])==list(FEATURE_NAMES)
            matrix=np.asarray([[f['features'][name] for name in FEATURE_NAMES]],dtype=np.float64)
            assert f['model_probability']==pytest.approx(float(pipeline.predict_proba(matrix)[0,1]))
        assert 'uncalibrated' in risk['message'] and '/tmp/' not in response.text
        assert data['structural']['functions'] and data['knowledge_graph']['nodes']


def test_live_classification_uses_the_recorded_inclusive_half_threshold(monkeypatch):
    """Boundary-only mock, not training labels or a claimed empirical model result."""
    import io,zipfile
    from types import SimpleNamespace
    import numpy as np
    from fastapi.testclient import TestClient
    from app.main import app
    class BoundaryPipeline:
        def predict_proba(self,values):return np.asarray([[1-p,p] for p in [.49,.50,.51]])
        def predict(self,values):return np.asarray([0,0,1])  # native argmax chooses class0 on a tie
    pipeline=BoundaryPipeline()
    monkeypatch.setattr('app.ml.repository.SERVICE',SimpleNamespace(load=lambda:pipeline,metadata={'model_version':'boundary-test-only'}))
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,'w') as z:z.writestr('boundary.c','int a(void){return 0;}\nint b(void){return 1;}\nint c(void){return 2;}')
    with TestClient(app) as client:
        r=client.post('/api/analyze',files={'file':('boundary.zip',stream.getvalue())})
        assert r.status_code==200
        functions=r.json()['defect_risk']['functions']
        assert [f['model_probability'] for f in functions]==[.49,.50,.51]
        assert [f['predicted_class'] for f in functions]==[0,1,1]
