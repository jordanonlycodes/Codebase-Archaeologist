# Academic report — Task 3B

- [Submission PDF](Codebase_Archaeologist_Report.pdf): **28 A4 pages**.
- [Editable DOCX](Codebase_Archaeologist_Report.docx): the same substantive text, tables and nine figures. Its designed pagination follows the PDF, but Word/LibreOffice may repaginate.
- [Evidence manifest](report_manifest.json): source and output SHA-256 hashes.
- [Automated document validation](validation.json): structure, text, metrics, completeness and bounds checks.

The report is prepared for Bilal Malik, 24P-3061, Software Engineering (SE), Class 5A, FAST-NUCES, Peshawar, 2026. Individual/instructor-approved participation details were supplied by the student. It documents the actual Task 1–3A implementation at `ce5d032216274d24800e61ca392c674426442851`. It does not certify independent institutional approval or claim future features are implemented.

All 19 requested academic sections are present. Nine captioned figures comprise five EDA presentations (two using selected panels of saved plots), the saved validation/test confusion matrices, and three original implementation diagrams: architecture, training/selection, and inference. Original experimental plots retain their source colors; report framing and original diagrams use Black & Crimson. There are no fabricated UI screenshots. The normal browser capture remained blocked by sandbox socket restrictions.

## Reproduce

From the project root with the existing ML plotting dependencies installed:

```bash
.venv/bin/python tools/generate_report.py
.venv/bin/python tools/validate_report.py
```

Generation uses only saved JSON/PNG evidence, Matplotlib, Pillow and standard-library DOCX/ZIP XML packaging. It does not import an estimator, deserialize a model, load raw datasets, train, or rerun held-out evaluation. Local artifact metadata is checked against tracked reports when available. Document binaries may differ across runs because of container timestamps and library versions; content is evidence-driven and shared between formats.

Validation additionally requires Poppler's `pdftotext` (Ubuntu package `poppler-utils`). It checks all saved validation/test metrics, section presence, shared substantive paragraphs, DOCX XML and relationships, nine embedded figures, 28 nonempty PDF pages, source/output hashes and PDF text bounds.

## Layout review and limits

All 28 PDF pages were rendered with Poppler and reviewed in contact sheets; figure/table pages were additionally inspected at higher resolution. No blank pages, overlapping text, broken tables or clipped text were found in the inspected PDF. The final layout uses an A4 grid, a dark bespoke cover, light body pages, crimson accents, captions, headers/footers and page numbers.

DOCX ZIP/XML/image relationships and editable text were validated. LibreOffice is present but its headless conversion exited unsuccessfully in this sandbox; therefore **DOCX visual rendering and actual Word pagination were not verified**. Its contents page intentionally states that page references follow the submission PDF. Open the DOCX in Word/LibreOffice before editing or submitting that format, and check repagination after edits. The PDF is the fixed-layout submission copy.

Previously verified application outcomes (73 / 120 / 140 tests by task) are cited as historical implementation evidence, not a newly executed test run. No application files or training artifacts were changed for Task 3B. The report explicitly states uncertainty, noisy labels, remaining shared commits, C-only inference, parser abstention, uncalibrated probabilities and missing-model behavior.
