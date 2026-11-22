"""Read-only local academic evidence audit. No fitting, held-out prediction or network.

Run: PYTHONPATH=. .venv/bin/python tools/audit_academic_evidence.py
Requires the existing trusted Task2 raw/prepared/model files; outputs counts/hashes only.
Assertions deliberately report stale report source hashes separately from output integrity.
"""
from pathlib import Path
import json,hashlib,numpy as np,pyarrow.parquet as pq
from app.ml.acquire import verify_manifest
from app.ml.dataset import load_split,clean_development
from app.ml.features import feature_matrix,FEATURE_NAMES,feature_schema
from app.ml.model_store import load_pipeline
from app.ml.io import digest
raw=Path('data/raw/devign');prep=Path('data/processed/devign-v1');run=Path('artifacts/devign-v1');reports=Path('reports/ml')
source=verify_manifest(raw);saved=json.loads((reports/'cleaning_audit.json').read_text())
train=load_split(raw,'train');val=load_split(raw,'validation');test=load_split(raw,'test',include_target=False)
cleaned,audit,decisions=clean_development(train,val,test)
assert audit==saved;assert decisions==json.loads((prep/'cleaning_decisions.json').read_text())
prepmeta=json.loads((prep/'metadata.json').read_text())
for name,expected in prepmeta['files'].items():assert digest(prep/name)==expected,name
assert prepmeta['identity']['schema']==feature_schema()
for name,expected in json.loads((run/'complete.json').read_text())['checksums'].items():assert digest(run/name)==expected,name
index=json.loads((prep/'row_index.json').read_text())
with np.load(prep/'development.npz',allow_pickle=False) as data:
 sizes={name:list(data['X_'+name].shape) for name in ['train','validation']};missing={}
 for split in ['train','validation']:
  X=data['X_'+split];missing[split]=dict(zip(FEATURE_NAMES,np.isnan(X).sum(axis=0).tolist()))
  assert [r['id'] for r in cleaned[split]]==[r['id'] for r in index[split]]
  assert np.array_equal(data['y_'+split],np.array([int(r['target']) for r in cleaned[split]]))
  sample,status=feature_matrix(r['func'] for r in cleaned[split][:3]);assert np.array_equal(sample,X[:3],equal_nan=True)
 selected,meta=load_pipeline(run,trusted=True)
 assert np.allclose(selected.named_steps['impute'].statistics_,np.nanmedian(data['X_train'],axis=0))
 assert np.isfinite(selected.named_steps['impute'].transform(data['X_train'])).all()
 lr,_=load_pipeline(run/'candidates/logistic_regression',trusted=True)
 imputed=lr.named_steps['impute'].transform(data['X_train'])
 assert np.allclose(lr.named_steps['scale'].mean_,imputed.mean(axis=0))
 std=imputed.std(axis=0);assert np.allclose(lr.named_steps['scale'].scale_,np.where(std>0,std,1))
comparison=json.loads((reports/'model_comparison.json').read_text())
for name in comparison:
 assert json.loads((run/'candidates'/name/'metrics.json').read_text())==comparison[name]
 assert digest(run/'candidates'/name/'pipeline.joblib')==json.loads((run/'candidates'/name/'metadata.json').read_text())['pipeline_sha256']
assert json.loads((run/'model_comparison.json').read_text())==comparison
assert meta==json.loads((reports/'model_metadata.json').read_text())
assert json.loads((run/'test_evaluation.json').read_text())==json.loads((reports/'test_evaluation.json').read_text())
classes={}
for split in ['train','validation','test']:
 table=pq.read_table(raw/source['splits'][split][0],columns=['target']);labels=table['target'].to_pylist();classes[split]={'rows':len(labels),'0':labels.count(False),'1':labels.count(True)}
old=meta['training']['identity']['implementation'];changed=[n for n,h in old.items() if digest(Path('app/ml')/n)!=h]
experiment=json.loads((run/'experiment.json').read_text());assert all(digest(Path('app/ml')/n)==h for n,h in experiment['implementation'].items())
manifest=json.loads(Path('submission/report_manifest.json').read_text());mismatch=[n for n,h in manifest['source_sha256'].items() if not Path(n).exists() or digest(Path(n))!=h]
for n,h in manifest['outputs_sha256'].items():assert digest(Path('submission')/n)==h
result={'raw_manifest_verified':True,'raw_class_counts':classes,'cleaning_reproduced':True,'cleaning_decisions':len(decisions),'prepared_shapes':sizes,'feature_missing':missing,'row_index_verified':True,'sample_features_equal':True,'training_imputation_and_scaler_verified':True,'pipeline_sha256':meta['pipeline_sha256'],'model_version':meta['model_version'],'environment':meta['environment'],'candidate_checkpoints_verified':list(comparison),'preparation_code_hash_drift':changed,'report_source_hash_mismatches':mismatch,'report_output_hashes_match':True}
print(json.dumps(result,indent=2))
