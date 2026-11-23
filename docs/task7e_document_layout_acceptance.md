# Task7E document layout acceptance

Fresh isolated LibreOffice26.8.3.1 conversion succeeded, unlike old sandbox attempts:
`libreoffice -env:UserInstallation=file:///tmp/task7e-lo-profile --headless --convert-to pdf --outdir /tmp/task7e-office submission/Codebase_Archaeologist_Report.docx`.
The original46-page DOCX rendered to46pages with correct author metadata. Regenerated
screenshot-bearing DOCX is converted again to a different temporary output directory;
current page counts/digests and comparison results are recorded in reports/release/task7e/layout.json.
Canonical PDF is never overwritten by an engine comparison. Both documents retain
17chapters/five appendices,exact production RF/scientific limitations and confirmed authors.

Acceptance method:PDF XML/text/metric/source validators; embedded screenshot hash checks;
Poppler page thumbnails and full-size cover,lists,tables,scientific results,screenshot,
references and appendix samples. LibreOffice pagination may differ from canonical shared-
source PDF:that is not a requirement for pixel identity. No Microsoft Word use is claimed.
Final evidence distinguishes successful rendering and inspected pages from a physical
interactive Office review or full accessibility certification. Re-run conversion/checks
whenever content or screenshots change; old outputs are not current acceptance evidence.
