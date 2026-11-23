# Task7D — approved model portability

Original artifact is4,490,519 bytes (~4.3MiB; exact size in models/devign-v1/manifest.json),
well below GitHub's documented50MiB warning/100MiB block. It was ignored under artifacts/
and all *.joblib. The narrow exception now tracks only models/devign-v1/pipeline.joblib,
with original metadata/schema and digest; candidate/data caches remain ignored.

Approved SHA-256:
9988945c6c851e885f3942a406a4d6c7d704547797e266d6d0aed95520db74e6.
Version devign-v1-4a23cc304ca8;11features; inclusive0.5;C-only. Numerical sklearn tree
parameters contain no retained function bodies. The provider C-UDA §2.2/§5.5 explicitly
discusses models as Results provided they contain no more than de minimis Data; source
agreement is preserved and independently inspected from its official repository. This
supports the packaging decision, not blanket upstream rights or a new project license.
No raw data or unsupported candidate binary is published.

`python tools/install_model.py` verifies ALL three files before copying missing files to
the unchanged runtime default artifacts/devign-v1. It is idempotent, refuses different
existing files and never deserializes, downloads or trains. Tests cover corruption and
preservation. Install only from the reviewed project checkout. A checksum is not a digital
signature; joblib is executable serialization, not safe user input.

`python tools/release_smoke.py` proves actual service/API inference. The current execution
produced clamp_index .6446299251115485,class1;sum_values .4640631119969904,class0;
entry .44115041436869545,class0. Python-only input produced zero ML predictions. Nine
workspace routes and the shared source/graph response passed. These are unlabeled fixture
integration observations, not defect-ground-truth or generalization measurements.
Use --sandbox-polling only for the documented restricted socket-wakeup environment.

requirements-runtime.lock records the29-package inference/web closure of the actual
Python3.14.10/Linux environment, without PyArrow/training data/Matplotlib. Strict loader
numerical/parser checks are unchanged. Full research tests still require optional ML
requirements and local genuine data; no clean install is claimed to rerun the whole
research experiment offline. Independent environment results are in clean-install doc.

Production model/science/threshold was not retrained, replaced or weakened. If missing,
the existing service returns unavailable and preserves static analysis; no fallback score.
