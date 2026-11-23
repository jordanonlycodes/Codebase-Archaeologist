# Task7E release verification

Entry e4ece23,remote independently matched. Fresh baseline540passed/15.35s,0failed/skipped,
one existing Starlette/httpx warning. Real browser, notices, screenshots and document
rendering results are in reports/release/task7e and the Task7E evidence documents.
Final exact suite/Node/syntax counts and archive checks appear in submission/release_checks.json.
No tests removed/skipped or assertions weakened. README's old missing-screenshot assertion
now requires actual verified images. Added offline vendor integrity, reviewed allowlist,
tamper rejection,35notice inventory, screenshot/DOCX-byte parity and real-browser evidence
checks. Graph harness adds cancellation/race regression; all older cases remain.

Model SHA remains9988945c6c851e885f3942a406a4d6c7d704547797e266d6d0aed95520db74e6,
11features,C-only,score>=0.5. No retraining or new provider. Browser/source archives are
checked for credentials; no raw data,venv,profiles,caches or unapproved model is packaged.
New assets are the reviewed fixed UMD/MIT/receipt and conservative notice evidence.

Source/archive smoke uses a fresh extraction and trusted installed model; final source
commit,CRC,extraction and checksums are explicit in the package manifest. Repeat build is
verified at the same source commit. Package source revision and later manifest commit
are distinguished; no circular self-hash or false remote equality is asserted.

User answered yes to instructor acceptance of validation evaluation for3models and final-
test evaluation for selectedRF only. Report states actual protocol; no additional final-
test evaluation is invented. Physical hardware FPS,full WCAG,Microsoft Word and a separate
fresh Ubuntu OS remain outside scope,not silently marked passed.

The mutable task7e_progress.md operational journal is excluded from report-source hashes
to prevent a release-receipt/journal regeneration cycle. Scientific artifacts,application
code,report code and substantive acceptance documents remain hashed; no source validator
assertion is relaxed. Layout/output receipts are likewise derived evidence,not report inputs.
