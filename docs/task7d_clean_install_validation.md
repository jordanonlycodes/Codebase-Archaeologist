# Task7D — clean installation validation

## Actually performed

A fresh standard venv at a temporary path (include-system-site-packages=false) was created
with Python3.14.10.29exact runtime wheels were recovered byte-for-byte from the existing
trusted pip HTTP cache, identified by their wheel METADATA/WHEEL tags, and installed via:

```
python -m venv /tmp/task7d-clean-venv
/tmp/task7d-clean-venv/bin/python -m pip install --no-index --find-links /tmp/task7d-wheelhouse -r requirements-runtime.lock
/tmp/task7d-clean-venv/bin/python -m pip check
```

All29packages installed; pip check found no broken requirements. No PyArrow/Matplotlib
was installed. A `git archive` of model-packaging commit4f9127a was extracted to a fresh
source tree without .git,.venv,data or developer artifacts. That checkout's own installer
copied its packaged approved model. Its own API smoke loaded genuine RF,returned the
three established fixture estimates,zero Python predictions and nine working workspace
routes. No developer dataset, model cache or original-site-packages was used. A later
release-source check repeats this against the final tooling/README checkpoint.

This is a real isolated install/source test on the same Linux host/interpreter, NOT a
new Ubuntu OS image or public-PyPI download test. Cached wheel origins were not freshly
revalidated over network and wheels are not redistributed. Terminal DNS blocks npm/GitHub.
Minimal runtime pins and direct clean-checkout smoke are stronger evidence than testing
only the existing development venv, but do not certify all Python/Ubuntu versions.

Clean Uvicorn completed startup, then localhost bind failed (exit3). Chromium exited
signal5 before HTML rendering at setsockopt:Operation not permitted. Thus startup/import
and in-process APIs pass; physical server/browser/GPU/mobile acceptance remains pending.

## Evaluator commands (networked Linux, tested Python3.14.10)

```bash
git clone https://github.com/jordanonlycodes/Codebase-Archaeologist.git
cd Codebase-Archaeologist
python3.14 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-runtime.lock
python tools/install_model.py
python tools/release_smoke.py --write-demo /tmp/university-demo.zip
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000. No cloud credential/training dataset is needed. These remote
clone/download commands require publication and networking; normal push is still attempted
at release end. Source archive is an alternative to cloning while publication is pending.
Optional3D is not redistributed pending provenance; use truthful2D fallback or complete
the vendor verification/install procedure. Exact lock pins are the supported recorded
runtime; using a generic older Python interpreter is not certified.

Research/development:install requirements-ml-frozen.txt and reproduce genuine dataset
instructions in docs/ml_pipeline.md if running data-dependent full tests. Node26.13.1
was used for frontend harnesses. No tests are removed/skipped to disguise absent data;
a fresh runtime-only install is verified by the separate smoke, not falsely by claiming
all research tests can run without their datasets/plotting dependencies.
