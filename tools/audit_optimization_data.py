"""Reproduce bounded optimization source diagnostics; never load test labels."""
from pathlib import Path
import numpy as np
from app.ml.optimization.audit import collect,audit
from app.ml.io import write_json
if __name__=='__main__':
    rows=collect(Path('data/raw/devign'),Path('data/processed/devign-v1'))
    report,groups,mask=audit(rows)
    out=Path('reports/ml/optimization/task7c0-v1');out.mkdir(parents=True,exist_ok=True)
    target=out/'dataset_quality.json'
    if target.exists():
        import json
        old=json.loads(target.read_text())
        if {k:v for k,v in old.items() if k!='seconds'}!={k:v for k,v in report.items() if k!='seconds'}:
            raise ValueError('Audit evidence changed; preserve run and use a new version')
    else: write_json(target,report)
    cache=Path('artifacts/devign-optimization/task7c0-v1');cache.mkdir(parents=True,exist_ok=True)
    if (cache/'audit.npz').exists():
        with np.load(cache/'audit.npz',allow_pickle=False) as saved:
            assert np.array_equal(saved['groups'],groups) and np.array_equal(saved['validation_mask'],mask)
    else: np.savez_compressed(cache/'audit.npz',groups=groups,validation_mask=mask)
    print(report,flush=True)
