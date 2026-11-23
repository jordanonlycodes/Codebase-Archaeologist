"""Reproduce bounded optimization source diagnostics; never load test labels."""
from pathlib import Path
import numpy as np
from app.ml.optimization.audit import collect,audit
from app.ml.io import write_json
if __name__=='__main__':
    rows=collect(Path('data/raw/devign'),Path('data/processed/devign-v1'))
    report,groups,mask=audit(rows)
    out=Path('reports/ml/optimization/task7c0-v1');out.mkdir(parents=True,exist_ok=True)
    write_json(out/'dataset_quality.json',report)
    cache=Path('artifacts/devign-optimization/task7c0-v1');cache.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(cache/'audit.npz',groups=groups,validation_mask=mask)
    print(report,flush=True)
