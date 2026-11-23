# Approved C-only research model

Exact existing Random Forest devign-v1-4a23cc304ca8,11features,score>=0.5.
Run `python tools/install_model.py` from repository root. This verifies the pinned SHA
and copies three files to the existing runtime artifacts/devign-v1 path. It refuses to
overwrite a different model. No dataset, network request or training is required.
Joblib is executable serialization: trust this project's reviewed artifact/Git source,
not an arbitrary upload. Checksums detect changes; they are not digital signatures.

The classifier contains numeric fitted tree parameters and no retained function bodies.
It was trained on the pinned CodeXGLUE/Devign numerical features. The provider's C-UDA
§2.2/§5.5 addresses models as Results when they do not contain more than de minimis Data.
The preserved agreement is C-UDA-1.0.md. This is the stated distribution basis, not blanket
upstream-source rights clearance or a new project-wide license. No raw dataset or
experimental candidate binary is distributed. See docs/task7d_model_portability.md.

Exact tested runtime is requirements-runtime.lock/Python3.14.10; broader compatibility
is not certified. Model loader enforces numerical/parser versions and feature order.
Historical exposed-test F1 .526316/AUC .587354 are modest research evidence; estimates
are uncalibrated and never confirmed defects/vulnerabilities. Python remains unscored.
