# Codebase Archaeologist — academic report / Task7D submission candidate

**Bilal Malik —24P-3061 · Aun Anis —24P-3017**

- [Editable Word report](Codebase_Archaeologist_Report.docx)
- [Matching substantive-content PDF](Codebase_Archaeologist_Report.pdf)
- [Evidence/output manifest](report_manifest.json)
- [Executed structural validation](validation.json)
- [Final release test and integrity record](release_checks.json)
- [Source/evidence matrix](../docs/task7c_report_evidence_matrix.md)
- [Screenshot capture and regeneration](../docs/task7c_screenshot_capture_guide.md)
- [Task 7D handoff](../docs/task7c_handoff_to_7d.md)

The revised report includes17chapters, authentic EDA/optimization plots, current architecture,
model comparison, controlled optimization and five appendices. Original Random Forest
remains deployed,11features,score>=0.5,C-only. No experimental model or improved production
performance is claimed. Existing exposed-test results and always-positive F1 limitation
are explicit. Figures are data plots/implementation diagrams, not fabricated screenshots.

## Regenerate and validate

Use the existing .venv with requirements-ml.txt (Matplotlib/Pillow) and Poppler utilities:

```bash
.venv/bin/python tools/generate_report.py
.venv/bin/python tools/validate_report.py
.venv/bin/python tools/check_report_links.py
```

Single editable content source:tools/report_content.py; existing shared PDF/OOXML renderer:
tools/generate_report.py. No benchmark fitting/inference or raw data loading occurs.
Build sources, evidence and outputs are hashed together; edit content/current paths first,
then regenerate. Do not merely change hashes to bypass stale evidence. Academic fields now come from academic_details.json; future confirmed changes should
update that record and regenerate; genuine screenshots are registered
in screenshots.json with provenance. Generated documents may differ in timestamps.

## Remaining submission acceptance

**Report status:PARTIALLY COMPLETED pending real screenshots and local office acceptance.**
Three explicit missing-screenshot paragraphs remain. All required academic fields are
now user-confirmed:FAST NUCES Peshawar,SE,AI-lab,M. Saad Khan,semester5,23November2026.
Old unconfirmed Class5A is removed; no individual roles are assigned.
Two-member permission is user-confirmed; no invented instructor approval document exists.
The official requirement “test each model” still needs instructor interpretation because
all original candidates have validation evaluation but only RF has final-test evaluation.

The PDF is fixed A4 layout. Word contains editable paragraphs, headings, tables, figures
and automatic PAGE fields. Contents/figure/table lists refer to PDF pagination; editing
or opening Word can repaginate. Fresh isolated LibreOffice conversion exited1 without
output here, so DOCX visual pagination is unverified. Shared substantive text, not identical
Office-suite rendering, is validated. The PDF is not PDF/UA certified/tagged; no claim of
accessible-document certification is made.

The current report's exact page/figure/table counts and validation status are in manifests
and Task7C docs. Team should inspect both files locally, complete screenshots/demo and
clean-machine model/vendor packaging during Task7D. Do not claim live browser/GitHub/GPU
acceptance based on automated suites. Prior report versions remain recoverable in Git.
