"""Development-only scientific invariants; no benchmark fitting/test-set tuning."""
import math
from pathlib import Path
import numpy as np
import pytest
from app.ml.features import extract_features,FEATURE_NAMES
from app.ml.optimization import features
from app.ml.optimization.audit import shape_tokens,shape_hash,grouped_ids,near_matches,shingles
from app.ml.optimization.experiment import metrics,thresholds,candidates,gate


def test_enhanced_schema_preserves_frozen_base_and_source_only_parity():
    source='int sum(int *a,int n){int total=0; /* note */ for(int i=0;i<n;i++){total+=a[i];} return total;}'
    result=np.asarray(features.extract(source));base=np.asarray(extract_features(source).values)
    assert len(result)==len(features.NAMES)==22
    np.testing.assert_allclose(result[:len(FEATURE_NAMES)],base,equal_nan=True)
    assert features.NAMES[:11]==FEATURE_NAMES
    named=dict(zip(features.NAMES,result));assert named['array_subscripts']==1 and named['assignments']==1
    assert named['comment_fraction']>0 and named['comparisons']==1
    np.testing.assert_array_equal(features.extract(source),features.extract(source))
    # Cached training rows and candidate inference both call exactly this callable.
    matrix=np.asarray([features.extract(source)])
    np.testing.assert_allclose(matrix[0],features.extract(source))
    assert 'target' not in features.NAMES and 'commit_id' not in features.NAMES


@pytest.mark.parametrize('source',[None,'','int broken( {','int a(void);'])
def test_missing_or_malformed_features_remain_missing_not_zero(source):
    values=features.extract(source)
    assert all(math.isnan(x) for x in values[11:])
    np.testing.assert_allclose(values[:11],extract_features(source).values,equal_nan=True)


def test_shape_audit_is_comment_and_name_insensitive_but_not_semantic_proof():
    a=shape_tokens('int foo(int x){return x+1;} // trailing')
    b=shape_tokens('int bar(int y){return y+9;}')
    assert shape_hash(a)==shape_hash(b) # Deliberate conservative grouping, not equal behavior.
    assert shape_tokens('char *s="// not a comment";')[-2:]==['S',';']


def test_grouping_connects_commit_and_clone_chains_without_labels():
    rows=[{'project':'p','commit_id':'a'},{'project':'p','commit_id':'a'},
          {'project':'p','commit_id':'b'},{'project':'other','commit_id':'a'}]
    ids=grouped_ids(rows,['x','y','y','z'])
    assert ids[0]==ids[1]==ids[2] and ids[3]!=ids[0]


def test_near_matches_verify_jaccard_and_bound_candidate_search():
    a=set(range(30));b=set(range(28))|{99,100}
    matched,report=near_matches([a,set(range(100,130))],[a,b,set(range(200,230))])
    assert matched=={0,1} and report['candidate_comparisons']<=3*50
    assert shingles(['a']*5)==set()


def test_operating_threshold_uses_fixed_training_oof_grid_and_preserves_inclusive_boundary():
    y=np.array([0,0,1,1]);p=np.array([.1,.49,.5,.9]);m=metrics(y,p,.5)
    assert m['confusion_matrix']==[[2,0],[0,2]] and m['f1']==1
    selected=thresholds(y,p);assert len(selected['grid'])==9
    assert selected['operating'] in [.3,.35,.4,.45,.5,.55,.6,.65,.7]
    assert 'OOF' in selected['rule']


def test_experiment_budget_and_training_only_preprocessing():
    models=candidates();assert len(models)==11
    assert len({(family,schema) for _,family,schema,_ in models})==7
    for _,_,_,model in models:
        assert model.steps[0][0]=='impute'
        assert not hasattr(model.named_steps['impute'],'statistics_')
        assert not hasattr(model.named_steps['classifier'],'classes_')
        assert model.named_steps['classifier'].get_params().get('n_jobs',1) in (None,1)  # LR lbfgs uses the outer single-thread BLAS limit.


def test_deployment_gate_rejects_f1_only_and_weak_evidence():
    baseline=metrics(np.array([0,0,1,1]),np.array([.1,.4,.6,.9]))
    row={'validation':{**baseline,'f1':1},'purged_validation':{**baseline,'rows':10},
         'f1_delta_interval':{'lower':-.1},'artifact_bytes':100,'inference_seconds':1,'baseline_inference_seconds':1}
    result=gate(row,baseline,baseline)
    assert result['numerical_gate_passed'] is False
    assert not result['checks']['purged_support_ge_300'] and not result['checks']['positive_bootstrap_lower']


def test_offline_experiment_has_no_test_evaluation_entry_point():
    source=Path('app/ml/optimization/experiment.py').read_text()
    assert 'test_once(' not in source and "load_split(raw,'test'" not in source
    assert 'test_labels_loaded' in source and 'StratifiedGroupKFold' in source


def test_completed_evidence_and_extractor_identity_are_intact():
    import hashlib,json
    root=Path('reports/ml/optimization/task7c0-v1')
    complete=json.loads((root/'complete.json').read_text())
    assert complete['completed']
    for name,checksum in complete['checksums'].items():
        assert hashlib.sha256((root/name).read_bytes()).hexdigest()==checksum
    protocol=json.loads((root/'protocol.json').read_text())
    for name,checksum in protocol['source_sha256'].items():
        assert hashlib.sha256((Path('app/ml/optimization')/name).read_bytes()).hexdigest()==checksum
    assert protocol['test_predictions']==0 and protocol['test_labels_loaded'] is False


def test_saved_selection_preserves_benchmark_and_rejects_all_finalists():
    import json
    root=Path('reports/ml/optimization/task7c0-v1')
    result=json.loads((root/'results.json').read_text())
    historical=json.loads(Path('reports/ml/model_comparison.json').read_text())
    assert result['baseline_validation']['f1']==historical['random_forest']['validation']['f1']
    assert result['test_predictions']==0 and result['numerical_gate_passers']==[]
    assert len(result['finalists'])==7
    assert result['baseline_validation']['rows']==2723
    assert result['baseline_purged_validation']['rows']==794
    for row in result['finalists'].values():
        assert row['serialization_roundtrip_equal'] and row['test_predictions']==0
        assert row['gate']==gate(row,result['baseline_validation'],result['baseline_purged_validation'])
        assert row['validation']['rows']==2723


def test_scientific_figures_are_tied_to_real_saved_results():
    import hashlib,json
    root=Path('reports/ml/optimization/task7c0-v1')
    manifest=json.loads((root/'figures.json').read_text())
    assert manifest['source_results_sha256']==hashlib.sha256((root/'results.json').read_bytes()).hexdigest()
    assert manifest['test_predictions']==0 and len(manifest['files'])==6
    for name,checksum in manifest['files'].items():
        assert hashlib.sha256((root/name).read_bytes()).hexdigest()==checksum
