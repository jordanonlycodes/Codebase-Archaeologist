#!/usr/bin/env python3
"""Real approved-model/API smoke from a checkout; no dataset/network/retraining."""
from pathlib import Path
import argparse,hashlib,io,json,sys,zipfile
ROOT=Path(__file__).resolve().parents[1]
def demo_bytes():
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,'w',zipfile.ZIP_DEFLATED) as archive:
        for name in ['review.c','helpers.py']:
            info=zipfile.ZipInfo(name,date_time=(2026,11,23,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            archive.writestr(info,(ROOT/'tests/fixtures/university_demo'/name).read_bytes())
    return stream.getvalue()
def smoke():
    sys.path.insert(0,str(ROOT))
    from fastapi.testclient import TestClient
    from app.main import app
    from app.ml.repository import SERVICE
    assert SERVICE.load() is not None,'Approved compatible model unavailable; install it and restart.'
    assert SERVICE.metadata['model_version']=='devign-v1-4a23cc304ca8'
    with TestClient(app) as client:
        assert client.get('/api/health').status_code==200
        for page in ['overview','risk','structure','graph','architecture','heatmaps','blast-radius','jordan','time-machine']:
            assert client.get('/workspace/'+page).status_code==200,page
        r=client.post('/api/analyze',files={'file':('university-demo.zip',demo_bytes())});assert r.status_code==200
        data=r.json();risk=data['defect_risk'];assert risk['analyzed_functions']==3
        assert {f['name'] for f in risk['functions']}=={'clamp_index','sum_values','entry'}
        assert all(f['path']=='review.c' and f['status']=='analyzed' and 0<=f['model_probability']<=1 for f in risk['functions'])
        assert data['summary']['files']==2 and data['knowledge_graph']['nodes']
        stream=io.BytesIO()
        with zipfile.ZipFile(stream,'w') as z:z.writestr('only.py','def helper(x): return x\n')
        py=client.post('/api/analyze',files={'file':('python.zip',stream.getvalue())}).json()
        assert py['defect_risk']['analyzed_functions']==0 and py['defect_risk']['functions']==[]
    return {'model_version':risk['model_version'],'files':2,'c_predictions':[{k:f[k] for k in ['name','model_probability','predicted_class']} for f in risk['functions']],
            'python_ml_predictions':0,'workspaces':9,'model_loaded':True,'source_body_execution':False,'dataset_required':False,'scope':'In-process API smoke, not a browser/GPU or live GitHub test.'}
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--sandbox-polling',action='store_true');parser.add_argument('--write-demo',type=Path);args=parser.parse_args()
    if args.sandbox_polling:
        import selectors
        Base=selectors.DefaultSelector
        class Polling(Base):
            def select(self,timeout=None):return super().select(.02 if timeout is None else min(timeout,.02))
        selectors.DefaultSelector=Polling
    if args.write_demo:
        args.write_demo.parent.mkdir(parents=True,exist_ok=True);args.write_demo.write_bytes(demo_bytes())
    print(json.dumps(smoke(),indent=2))
