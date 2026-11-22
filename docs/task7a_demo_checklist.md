# Task 7A — reproducible university demonstration checklist

This is a demonstration plan and actual API-evidence record, **not** an assertion that
a human has watched the running browser. Complete the unchecked browser items in7B.
No cloud key, live GitHub or raw dataset is required for the core local prediction demo.

## 1. Prepare the exact local environment

```bash
cd /home/jordan/Projects/codebase-archaeologist
source .venv/bin/activate
python -m pip check
PYTHONPATH=. python tools/audit_academic_evidence.py
```

The last command requires the existing genuine raw/prepared/checkpoint files and performs
read-only integrity checks; it does not train or reevaluate test. A demo machine needs the
trusted selected artifact, not all raw data. A fresh clone intentionally excludes model
binaries. Restore these three **trusted** files together under artifacts/devign-v1:
`pipeline.joblib`, `metadata.json`, `feature_schema.json`. Do not load uploaded/untrusted
Joblib. Expected selected pipeline SHA256:
`9988945c6c851e885f3942a406a4d6c7d704547797e266d6d0aed95520db74e6`.

The recorded environment is Python3.14.10 with scikit-learn1.9.1,numpy2.5.5,scipy1.18.1,
joblib1.6.0,tree-sitter0.25.2,tree-sitter-c0.24.2. Use requirements-ml-frozen.txt for that
recorded platform/environment; broad requirements-ml.txt ranges do not guarantee artifact
compatibility on another Python/version combination.7D must prove clean-machine setup.
Do not fix an unavailable model by training during a presentation.

## 2. Create the original, transparent demo ZIP

```bash
python - <<'PY'
from pathlib import Path
from zipfile import ZipFile
root=Path('tests/fixtures/university_demo')
with ZipFile('/tmp/codebase-university-demo.zip','w') as archive:
    for name in ['review.c','helpers.py']:
        archive.write(root/name,name)
print('/tmp/codebase-university-demo.zip')
PY
```

This original fixture is not a Devign sample or labeled defect benchmark. Show the C
source: clamp_index has conditionals, sum_values a loop, entry calls sum_values. The Python
helper demonstrates structural coverage without C-model predictions. Source is never
compiled/executed by the analyzer. Neither class0 nor class1 is known ground truth here.

## 3. Start and prove genuine model integration

```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

In a second terminal:

```bash
curl --fail-with-body -sS \
  -F 'file=@/tmp/codebase-university-demo.zip' \
  http://127.0.0.1:8000/api/analyze \
  -o /tmp/codebase-university-demo-result.json
python - <<'PY'
import json
from pathlib import Path
result=json.loads(Path('/tmp/codebase-university-demo-result.json').read_text())
print('Files:',result['summary']['files'])
print('ML:',result['defect_risk']['status'],result['defect_risk']['model_version'])
for f in result['defect_risk']['functions']:
    print(f['name'],f['path'],f['start_line'],f['end_line'],f['predicted_class'],f['model_probability'])
PY
```

Observed in-process audit with this exact artifact and ZIP contents:

| Entity | Expected actual observation |
| :-- | :-- |
| Inventory |2 files;4 structural functions;7 graph nodes |
| clamp_index,review.c:2–6 | class1,0.6446299251115485 |
| sum_values,review.c:8–14 | class0,0.4640631119969904 |
| entry,review.c:16–19 | class0,0.44115041436869545 |
| helpers.py | Structural analysis; no ML score |

Do not hardcode these scores into the UI or hide differences. If environment/artifact or
source changes, inspect and explain the actual returned values. The regression compares
returned features/scores directly to the selected saved pipeline. These are research
estimates, not demonstrated defects, calibrated certainty or an accuracy experiment.

## 4. Human browser acceptance — not yet verified here

- [ ] Open `/` and `/explore` at1366×768; import the generated ZIP through the actual UI.
- [ ] Overview reports2 files and retained provenance; open Risk without reuploading.
- [ ] Risk shows3 C functions, exact line locations,1 defect-related class/2 negative
      classes for this recorded run, actual estimated scores, explicit model limitations.
- [ ] Select a function; inspect all11 extracted metrics, status and location. Explain
      >=.5 decision rule and why a prediction is not a confirmed defect.
- [ ] Structure shows4 C/Python functions; Python is unscored, not low risk.
- [ ] In2D graph inspect real entry→sum_values CALLS and hierarchy. Optional3D requires
      local reviewed vendor assets/WebGL; missing3D must preserve2D. Camera issues belong7B.
- [ ] Visit architecture/heatmaps/impact, then return to Risk; same snapshot and IDs survive.
- [ ] Export JSON; verify actual defect_risk and original source metadata. No source bodies,
      credentials, fabricated file probabilities or separate analysis are expected.
- [ ] Refresh/back/forward and narrow layouts; keyboard focus, long paths and console errors.
- [ ] Jordan Local remains offline/evidence-grounded; no cloud provider is needed or enabled.
- [ ] ZIP Time Machine shows honest no-history, not fictional activity. GitHub/history is
      optional extended demo, not a dependency of the academic model workflow.

## 5. Show experimental evidence with correct split labels

Open reports/ml/model_comparison.json and explain all three **validation** results.
RF validation F1=.5209947003668977 is highest among these configurations. Separately open
test_evaluation.json: selected RF test F1=.5263157894736842,AUC=.5873540367979673,
confusion `[[842,635],[580,675]]`. Do not claim LR/HGB final-test numbers exist.
Show genuine dataset EDA plots/source manifest, shared ordered feature schema and the
C-only inference code. Mention overfitting gap, near-clone/shared-project limits and the
naive-positive F1 baseline; a higher candidate F1 is not proof of excellent performance.

## 6. Failure-handling demonstration

- [ ] Import a Python-only ZIP: static/structural results remain; no fabricated ML scores.
- [ ] Import JS-only source: inventory retained; unsupported structural/ML scope explicit.
- [ ] Invalid ZIP bytes:400 invalid_archive. Empty ZIP:422 empty_repository.
- [ ] Malformed C: partial coverage/parse issue rather than invented predictions.
- [ ] In a **separate process**, point ARCHAEOLOGIST_MODEL_DIR at a disposable empty
      directory and run a second server port. Import the same ZIP: unavailable ML,
      functioning static intelligence. Do not delete/mutate the real artifact. Restart
      normally afterward because model availability is cached per process.
- [ ] Invalid GitHub URL rejected before network. A valid GitHub flow is optional and
      depends on actual connectivity/quota; record failures honestly.

The forced-predictor-failure path is automated (safe temporary mock, HTTP200/partial,
no internal diagnostic leakage), not a reason to corrupt the real model for a live demo.

## 7. Commands and explicit outstanding signoffs

```bash
python -m pytest -q tests/test_academic_evidence.py tests/ml/test_repository.py
python -m pytest -q
```

Socket-restricted sandboxes use the existing selector wrapper in docs/ml_pipeline.md;
normal local environments should use ordinary pytest. The report validator currently
fails stale source hashes and must be legitimately regenerated/revalidated in7C.

Before university submission: obtain documentary solo exception/requirement5 interpretation,
complete browser demo/captures in7B, final report in7C and trusted artifact/vendor/environment
packaging in7D. No screenshot, live browser success or instructor approval is implied by
the in-process smoke results above.
