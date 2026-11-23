# Task7D — release baseline

Entry main HEAD:0facc5d9dd29ffb0bc5bfb2932663f8f10c4082d. Tracked clean; three existing
untracked graph assets preserved. Fresh baseline530passed,0failed/skipped,104.29s;
one existing Starlette/httpx warning. Tests use the previously documented process-local
polling selector wrapper; no app networking patch. Actual application entry:
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000.

Tested Python3.14.10/Linux x86_64, exact ML versions in requirements-ml-frozen.txt.
requirements.txt broadly constrains web/test packages; requirements-ml.txt adds optional
training/plotting dependencies. Production loader requires exact numpy2.5.5/scipy1.18.1/
sklearn1.9.1/joblib1.6.0 and schema parser versions tree-sitter0.25.2/Cgrammar0.24.2.
A minimal exact runtime closure will be recorded separately, without bulk upgrades.

Trusted model:ignored artifacts/devign-v1/pipeline.joblib (~4.3MiB), metadata.json,
feature_schema.json. No dataset is needed for inference. Raw/prepared data and experimental
candidate models remain ignored; no first-run training. Default path remains unchanged.
Optional operator-only ARCHAEOLOGIST_MODEL_DIR overrides that path. CODEBASE_GITHUB_TOKEN
is optional public-history API authentication. Jordan cloud env exists but is deferred;
no keys/providers are configured for this release and Local mode needs none.

Report:46-page PDF/editable DOCX,17chapters,5appendices,11figures,13tables. Original
pipeline SHA9988945c6c851e885f3942a406a4d6c7d704547797e266d6d0aed95520db74e6.
Task7C pending UI screenshots/Office layout/manual demo; model/vendor portability also
requires work. Academic fields are now explicitly user-confirmed:FAST NUCES Peshawar,
SE, AI-lab, M. Saad Khan, semester5,23November2026; both existing authors unchanged.
Section/Class5A was not confirmed and must not be asserted as a release academic field.

Graph bundle691294bytes, observed SHA19b3be27040fc894e56d684d53c5f62526c25e5d27f37e8fe91fafff605e4ef4.
Its receipt/toplevelMIT license exist; no archive/transitive-version lock is locally
available. Fresh npm retrieval failed DNS. Do not stage these files solely on filename/
receipt authority. Local3D remains intact; clean/offline3D redistribution is unresolved.

No project-wide LICENSE found. Do not silently select a new project license. Noto fonts
have a local SIL OFL notice. Model/provider and graph/license evidence will be documented.
