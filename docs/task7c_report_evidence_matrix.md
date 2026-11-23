# Task 7C — report/evidence and academic requirements matrix

Current scope is17chapters plus front matter/references/five appendices. Exact metrics
are consumed from saved JSON rather than copied from promotional summaries. No training
or new test prediction is performed by report generation.

| University criterion | Report location | Primary repository evidence | Status / remaining limitation |
|---|---|---|---|
|1 Problem statement|Ch1–2|README.md; app/routes/analysis.py; app/analysis/models.py|PASS; source facts and C-only prediction distinguished.|
|2 Dataset/source/features/target|Ch4; AppA|reports/ml/source_manifest.json; app/ml/acquire.py; app/ml/features.py; reports/ml/feature_schema.json|PASS; pinned Parquet, provider labels, C-only numeric predictors, attribution limitations.|
|3 Missing/duplicates/encoding/scaling/splits|Ch5,8–9|app/ml/dataset.py; prepare.py; estimators.py; reports/ml/cleaning_audit.json; tests/ml/test_dataset.py|PASS; categorical predictors N/A, tree scaling N/A, LR training-only scaling; imputation retained.|
|4 EDA|Ch6|reports/ml/eda_summary.json; observations.txt; feature_distributions.png; feature_correlations.png; missing_and_duplicates.png|PASS; genuine development evidence, not app heatmaps.|
|5 Train/test2–4 models|Ch8–10; AppC|app/ml/train.py; estimators.py; reports/ml/model_comparison.json; test_evaluation.json; optimization/task7c0-v1|PARTIAL under literal final-test-for-each wording;3 original models validation-evaluated, only RF final-test evaluated. Four families in optimization. Instructor interpretation still needs confirmation.|
|6 Compare/select/understand|Ch8–10|Original metrics; app/ml/optimization/experiment.py; protocol/results/selection_decision JSON|PASS with modest-performance caveats; full unfavorable comparisons, always-positive baseline, gate rejection.|
|7 Integrated app|Ch7,11–14; AppB/E|app/ml/repository.py; model_store.py; routes/analysis.py; tests/ml/test_repository.py; tests/test_product.py|IMPLEMENTED/automated verified; real browser/demo acceptance is separate.|
|8 Source/report/dataset/demo|Front; References; AppB/E|submission/*.docx/pdf; README; dataset/source URLs; tests/fixtures/university_demo|PARTIAL pending academic fields, authentic screenshots/demo and Task7D packaging.|
|Group rule|Declaration|User confirms permitted two-member group; original requirements says3|Both actual members named; no approval document/third member fabricated.|

## Authoritative requirements and academic identity

Original PDF inspected with pdftotext at /home/jordan/Downloads/AI Project Requirements.pdf.
SHA-256 is recorded below. It contains all eight criteria and three-member wording,
but no institution/course/instructor/semester fields. It is not redistributed.
Existing report's FAST-NUCES,Peshawar /SE /Class5A record is retained with confirmation
notice; no new academic detail is inferred. Course/instructor/semester/date remain editable.
Members:Bilal Malik—24P-3061 and Aun Anis—24P-3017, no role allocation.

## Implemented application evidence

- Shared pipeline: app/routes/analysis.py:analyze_archive; app/ingestion/archive.py and
  github.py; app/analysis/scanner.py; structural.py; graph/engine.py; architecture/engine.py.
- Dedicated routes/assets: app/routes/dashboard.py:PAGES/ASSETS; app/templates/workspace.html
  and workspace_base.html; app/static/product/{store,workspace,common,import}.js.
- Graph: app/analysis/graph/{models,builder,resolution,engine}.py;
  app/static/graph/{data,layouts,svg,three,explorer}.js.
- Architecture/heatmaps: app/analysis/architecture/engine.py; app/static/architecture/.
  Cycles use imports/includes only, grouping direct-parent file membership.
- Impact: app/static/impact/engine.js and explorer.js; actual paths,1–3hops, membership
  is not propagation. tests/test_impact.py and tests/frontend/impact.test.cjs.
- Jordan Local: app/static/jordan/{retrieval,local,workspace}.js; optional configured
  app/jordan/provider.py and routes/jordan.py remain consent-gated and not live verified.
- History: app/history/{github,core,models,cache,status}.py; routes/history.py;
  app/static/time_machine/. Pinned24commit window, tree/diff limits, scope-aware cache.
- Motion/branding: app/static/product/motion.js/css; app/static/brand/; docs/task7b1_*.
  Contract/harness tests are not physical GPU/rendered-layout acceptance.

## ML and figure evidence

Production:model_metadata.json /feature_schema.json /test_evaluation.json under reports/ml.
Local trusted artifacts/devign-v1/pipeline.joblib stays ignored, unchanged. Experimental
22features are isolated in app/ml/optimization/features.py; all24,473base prefixes checked.
Original held-out results remain exposed historical results, never a new blind test.
New clone audit:app/ml/optimization/audit.py and versioned dataset_quality.json.
CV/OOF/gates:experiment.py plus protocol/folds/shortlist/*-validation/results JSON.
Six optimization PNGs have figures.json checksums; plots use actual saved development data.
Original EDA images retain source pixels; cropped panels are labeled as selected originals.
Architecture/training diagrams are generated from reviewed source structure, not UI captures.

## Reference verification

submission/references.json records eight numbered primary sources and inspection status.
Metadata checked through available web retrieval: Devign proceedings, CodeXGLUE arXiv,
Breiman publisher DOI, provider card/task page, sklearn, Tree-sitter, GitHub and FastAPI
official docs. No invented DOI/page count or derivative benchmark comparison is inserted.
Network-free link checker validates local links/figures; this is not a new live GitHub
application smoke test. URLs are printed in both documents for traceability.

Original requirements PDF SHA-256: `1091b0b68088c5858227bc4e4534832283b73bef4ee7b0992e37be7c7fb006e8`.
