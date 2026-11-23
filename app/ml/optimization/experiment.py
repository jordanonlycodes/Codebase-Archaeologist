"""Locked offline development experiments. No path loads or predicts test targets."""
from pathlib import Path
from collections import defaultdict
import argparse,json,time,warnings,hashlib
import joblib,numpy as np
from sklearn.base import clone
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.metrics import (accuracy_score,balanced_accuracy_score,precision_score,recall_score,
                            f1_score,roc_auc_score,average_precision_score,confusion_matrix)
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from threadpoolctl import threadpool_limits
from app.ml.estimators import build_models,model_parameters
from app.ml.model_store import load_pipeline,environment_versions
from app.ml.features import FEATURE_NAMES
from app.ml.io import read_json,write_json,digest
from app.ml.optimization import features
from app.ml.optimization.audit import collect,grouped_ids,shape_tokens,shape_hash

SEED=42
GRID=np.round(np.arange(.30,.701,.05),2)
REPORT=Path('reports/ml/optimization/task7c0-v1')
CACHE=Path('artifacts/devign-optimization/task7c0-v1')


def metrics(y,p,threshold=.5):
    prediction=(np.asarray(p)>=threshold).astype(int)
    return {'rows':len(y),'threshold':float(threshold),'accuracy':float(accuracy_score(y,prediction)),
            'balanced_accuracy':float(balanced_accuracy_score(y,prediction)),
            'precision':float(precision_score(y,prediction,zero_division=0)),
            'recall':float(recall_score(y,prediction,zero_division=0)),
            'f1':float(f1_score(y,prediction,zero_division=0)),
            'roc_auc':float(roc_auc_score(y,p)) if len(np.unique(y))==2 else None,
            'average_precision':float(average_precision_score(y,p)),
            'positive_prediction_fraction':float(np.mean(prediction)),
            'confusion_matrix':confusion_matrix(y,prediction,labels=[0,1]).tolist()}


def thresholds(y,p):
    rows=[metrics(y,p,t) for t in GRID]
    order=lambda r:(-r['f1'],-r['precision'],abs(r['threshold']-.5),r['threshold'])
    eligible=[r for r in rows if r['precision']>=.50 and r['recall']>=.20]
    operating=min(eligible,key=order)['threshold'] if eligible else .5
    return {'grid':rows,'unconstrained':min(rows,key=order)['threshold'],
            'operating':operating,'rule':'Training OOF F1 maximum with precision>=.50 and recall>=.20; else .5.'}


def candidates():
    models=build_models();out=[]
    def add(name,family,schema,base,params):
        model=clone(models[base]);model.set_params(**{'classifier__'+k:v for k,v in params.items()})
        out.append((name,family,schema,model))
    add('v1_lr_unweighted_c01','lr','v1','logistic_regression',{'C':.1,'class_weight':None})
    add('v1_lr_balanced_c10','lr','v1','logistic_regression',{'C':10.0})
    add('v1_rf_baseline','rf','v1','random_forest',{})
    add('v1_rf_deeper_unweighted','rf','v1','random_forest',{'max_depth':18,'min_samples_leaf':5,'class_weight':None,'max_features':.7})
    add('v1_hgb_baseline','hgb','v1','hist_gradient_boosting',{})
    add('v1_hgb_regularized','hgb','v1','hist_gradient_boosting',{'max_iter':240,'max_leaf_nodes':31,'l2_regularization':5.0,'class_weight':None})
    add('v2_lr_balanced','lr','v2','logistic_regression',{})
    add('v2_rf_baseline_shape','rf','v2','random_forest',{})
    add('v2_rf_deeper_unweighted','rf','v2','random_forest',{'max_depth':18,'min_samples_leaf':5,'class_weight':None,'max_features':.7})
    add('v2_hgb_regularized','hgb','v2','hist_gradient_boosting',{'max_iter':240,'max_leaf_nodes':31,'l2_regularization':5.0,'class_weight':None})
    extra=Pipeline([('impute',SimpleImputer(strategy='median',keep_empty_features=True)),('classifier',ExtraTreesClassifier(n_estimators=160,max_depth=16,min_samples_leaf=4,class_weight='balanced',n_jobs=1,random_state=SEED))])
    out.append(('v2_extra_trees','extra_trees','v2',extra));return out


def paired_interval(y,new,old,groups,repeats=200):
    # Cluster bootstrap respects known project/commit+shape connections in validation.
    unique=np.unique(groups);indices=[np.flatnonzero(groups==g) for g in unique];rng=np.random.default_rng(SEED);deltas=[]
    for _ in range(repeats):
        sample=np.concatenate([indices[i] for i in rng.integers(0,len(indices),len(indices))])
        deltas.append(f1_score(y[sample],new[sample],zero_division=0)-f1_score(y[sample],old[sample],zero_division=0))
    return {'method':'200 paired validation-cluster bootstrap resamples, seed42; development uncertainty, not blind confirmation.',
            'lower':float(np.percentile(deltas,2.5)),'upper':float(np.percentile(deltas,97.5))}


def timed_prediction(model,X):
    model.predict_proba(X[:10]) # Warm only on development inputs.
    timings=[]
    for _ in range(5):
        t=time.perf_counter();prob=model.predict_proba(X)[:,1];timings.append(time.perf_counter()-t)
    return prob,float(np.median(timings))


def gate(row,baseline,purged_baseline):
    m=row['validation'];p=row['purged_validation'];ci=row['f1_delta_interval']
    checks={'f1_gain_ge_02':m['f1']-baseline['f1']>=.02,'positive_bootstrap_lower':ci['lower']>0,
            'precision_ge_50':m['precision']>=.50,'auc_not_worse':m['roc_auc']>=baseline['roc_auc'],
            'accuracy_within_01':m['accuracy']>=baseline['accuracy']-.01,
            'balanced_accuracy_not_worse':m['balanced_accuracy']>=baseline['balanced_accuracy'],
            'purged_support_ge_300':p['rows']>=300,'purged_f1_not_worse':p['f1']>=purged_baseline['f1'],
            'artifact_le_16mib':row['artifact_bytes']<=16*1024*1024,
            'latency_le_25ms_per_function':row['inference_seconds']/m['rows']<=.025,
            'latency_le_2x_baseline':row['inference_seconds']<=2*row['baseline_inference_seconds']}
    return {'checks':checks,'numerical_gate_passed':all(checks.values()),
            'deployment_requires':'Separate strict runtime schema/loader/C-only/parity/rollback acceptance; numerical pass is not automatic deployment.'}


def run(max_seconds=900):
    start=time.perf_counter();REPORT.mkdir(parents=True,exist_ok=True);CACHE.mkdir(parents=True,exist_ok=True)
    configurations=candidates()
    identity={'protocol':'task7c0-v1','seed':SEED,'folds':3,'threads':1,'max_fit_seconds':max_seconds,
              'test_predictions':0,'test_labels_loaded':False,'threshold_grid':GRID.tolist(),
              'prepared_sha256':digest(Path('data/processed/devign-v1/development.npz')),
              'audit_sha256':digest(CACHE/'audit.npz'),'dataset_quality_sha256':digest(REPORT/'dataset_quality.json'),
              'source_sha256':{p.name:digest(p) for p in Path(__file__).parent.glob('*.py')},
              'environment':environment_versions(),
              'configurations':{n:{'family':f,'schema':s,'parameters':model_parameters(m)} for n,f,s,m in configurations}}
    identity_path=REPORT/'protocol.json'
    if identity_path.exists() and read_json(identity_path)!=identity:raise ValueError('Run identity changed; use a new version, do not overwrite results.')
    write_json(identity_path,identity)
    if (REPORT/'complete.json').exists():
        
        complete=read_json(REPORT/'complete.json')
        for filename,checksum in complete['checksums'].items():
            if digest(REPORT/filename)!=checksum:raise ValueError('Completed evidence checksum mismatch')
        print('Completed run retained; no retraining or validation recomputation.');return
    def deadline():
        if time.perf_counter()-start>max_seconds:raise TimeoutError('Cooperative experiment deadline reached between bounded fits.')
    data=np.load('data/processed/devign-v1/development.npz',allow_pickle=False)
    audit=np.load(CACHE/'audit.npz',allow_pickle=False);groups=audit['groups'];mask=audit['validation_mask']
    rows=collect(Path('data/raw/devign'),Path('data/processed/devign-v1'))
    enhanced=CACHE/'enhanced.npz';extraction_started=time.perf_counter()
    feature_identity={'code':digest(Path(features.__file__)),'prepared':identity['prepared_sha256']}
    if enhanced.exists():
        receipt=read_json(CACHE/'enhanced.json')
        if receipt['identity']!=feature_identity or receipt['sha256']!=digest(enhanced):raise ValueError('Enhanced feature cache mismatch')
    else:
        arrays={k:np.asarray([features.extract(r['func']) for r in rows[k]],dtype=np.float64) for k in ['train','validation']}
        np.savez_compressed(enhanced,**arrays)
        write_json(CACHE/'enhanced.json',{'identity':feature_identity,'sha256':digest(enhanced)})
    v2=np.load(enhanced,allow_pickle=False);y=data['y_train'];yv=data['y_validation']
    assert np.allclose(v2['train'][:,:len(FEATURE_NAMES)],data['X_train'],equal_nan=True)
    assert np.allclose(v2['validation'][:,:len(FEATURE_NAMES)],data['X_validation'],equal_nan=True)
    write_json(REPORT/'feature_schema.json',features.schema())
    folds=list(StratifiedGroupKFold(n_splits=3,shuffle=True,random_state=SEED).split(data['X_train'],y,groups))
    for a,b in folds:assert not set(groups[a])&set(groups[b])
    write_json(REPORT/'folds.json',{'rows':len(y),'unique_groups':len(set(groups)),
               'folds':[{'train':len(a),'evaluation':len(b),'positive_fraction':float(np.mean(y[b])),
                         'evaluation_indices_sha256':hashlib.sha256(b.tobytes()).hexdigest()} for a,b in folds]})
    summary={};fit_start=time.perf_counter()
    with threadpool_limits(limits=1):
        for name,family,schema,model in configurations:
            deadline();saved=REPORT/(name+'.json');oof_path=CACHE/(name+'-oof.npy')
            if saved.exists():summary[name]=read_json(saved);continue
            X=data['X_train'] if schema=='v1' else v2['train'];oof=np.zeros(len(y));measure=[];caught=[]
            print('CV',name,flush=True)
            for fold,(a,b) in enumerate(folds):
                deadline();pipeline=clone(model);t=time.perf_counter()
                with warnings.catch_warnings(record=True) as ws:
                    warnings.simplefilter('always');pipeline.fit(X[a],y[a])
                seconds=time.perf_counter()-t;prob=pipeline.predict_proba(X[b])[:,1];oof[b]=prob
                measure.append({'fold':fold,'fit_seconds':seconds,'metrics':metrics(y[b],prob)})
                caught.extend(sorted({str(w.message) for w in ws}))
            row={'name':name,'family':family,'schema':schema,'folds':measure,'cv_mean_f1':float(np.mean([f['metrics']['f1'] for f in measure])),
                 'cv_std_f1':float(np.std([f['metrics']['f1'] for f in measure])),'oof':metrics(y,oof),
                 'threshold_selection':thresholds(y,oof),'warnings':sorted(set(caught)),
                 'fit_seconds':sum(f['fit_seconds'] for f in measure)}
            np.save(oof_path,oof,allow_pickle=False);write_json(saved,row);summary[name]=row
        finalists={}
        for name,family,schema,model in configurations:
            key=family+':'+schema
            if key not in finalists or (-summary[name]['cv_mean_f1'],name)<(-summary[finalists[key]]['cv_mean_f1'],finalists[key]):finalists[key]=name
        write_json(REPORT/'shortlist.json',{'rule':'Max training grouped-CV mean F1 at .5 per family/schema; alphabetical ties; before validation.', 'finalists':finalists})
        baseline,_=load_pipeline(Path('artifacts/devign-v1'),trusted=True)
        baseline_prob,baseline_seconds=timed_prediction(baseline,data['X_validation'])
        base=metrics(yv,baseline_prob);assert abs(base['f1']-read_json(Path('reports/ml/model_comparison.json'))['random_forest']['validation']['f1'])<1e-12
        baseline_purge=metrics(yv[mask],baseline_prob[mask]);val_groups=grouped_ids(rows['validation'],[shape_hash(shape_tokens(r['func'])) for r in rows['validation']])
        np.savez_compressed(CACHE/'baseline-validation.npz',probabilities=baseline_prob,labels=yv)
        evaluation={}
        for name in finalists.values():
            deadline();_,family,schema,model=next(c for c in configurations if c[0]==name);saved=REPORT/(name+'-validation.json')
            if saved.exists():evaluation[name]=read_json(saved);continue
            X=data['X_train'] if schema=='v1' else v2['train'];V=data['X_validation'] if schema=='v1' else v2['validation'];t=time.perf_counter()
            model.fit(X,y);fit_seconds=time.perf_counter()-t;prob,seconds=timed_prediction(model,V)
            threshold=summary[name]['threshold_selection']['operating'];output=CACHE/(name+'.joblib');joblib.dump(model,output,compress=3)
            reloaded=joblib.load(output);assert np.array_equal(reloaded.predict_proba(V[:10]),model.predict_proba(V[:10]))
            row={'name':name,'family':family,'schema':schema,'feature_names':list(FEATURE_NAMES) if schema=='v1' else list(features.NAMES),
                 'fit_seconds':fit_seconds,'inference_seconds':seconds,'baseline_inference_seconds':baseline_seconds,
                 'artifact_path':str(output),'artifact_sha256':digest(output),'artifact_bytes':output.stat().st_size,
                 'validation':metrics(yv,prob,threshold),'validation_at_half':metrics(yv,prob),
                 'purged_validation':metrics(yv[mask],prob[mask],threshold),
                 'f1_delta_interval':paired_interval(yv,prob>=threshold,baseline_prob>=.5,val_groups),
                 'threshold':threshold,'test_predictions':0,'serialization_roundtrip_equal':True}
            row['gate']=gate(row,base,baseline_purge);np.save(CACHE/(name+'-validation.npy'),prob,allow_pickle=False)
            write_json(saved,row);evaluation[name]=row;print('VALIDATION',name,row['validation'],row['gate'],flush=True)
    winner=max(evaluation,key=lambda n:(evaluation[n]['validation']['f1'],evaluation[n]['validation']['roc_auc'],n))
    result={'baseline_validation':base,'baseline_purged_validation':baseline_purge,
            'always_positive_validation':metrics(yv,np.ones(len(yv))),
            'majority_negative_validation':metrics(yv,np.zeros(len(yv))),
            'finalists':evaluation,'highest_validation_f1':winner,
            'numerical_gate_passers':[n for n in evaluation if evaluation[n]['gate']['numerical_gate_passed']],
            'features_extraction_seconds':fit_start-extraction_started,'fitting_and_gate_seconds':time.perf_counter()-fit_start,
            'total_seconds':time.perf_counter()-start,'test_predictions':0,
            'note':'Repeated development validation is not an independent test; no new official test evaluation.'}
    write_json(REPORT/'results.json',result)
    write_json(REPORT/'complete.json',{'checksums':{p.name:digest(p) for p in REPORT.glob('*.json') if p.name!='complete.json'},'completed':True})
    print('DONE',json.dumps({k:v for k,v in result.items() if k!='finalists'}),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--max-seconds',type=int,default=900)
    run(parser.parse_args().max_seconds)
