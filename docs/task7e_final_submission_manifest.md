# Task7E submission manifest

Rebuild with `python tools/build_submission.py` after committing current reviewed sources.
submission/final/manifest.json records exact source commit,all payload SHA256/bytes,
archive CRC/extracted-hash checks and generation date. Final/candidate status is driven
by explicit release acceptance; never inferred from a ZIP existing. The final package
contains current Word/PDF,actual screenshots,approved model/schema,offline3D/root MIT,
conservative dependency notices,setup/demo,academic fields and verification records.
source.zip is a separate clean committed snapshot; excludes .git,venv,data,caches,secrets,
unrelated binaries/archives. Only reviewed graph files bypass default vendor exclusion.

Exact names/sizes/digests are in manifest.json instead of manually copied numbers that
would go stale after report changes. Older ignored candidate archives are historical
outputs,not current submission instructions. Deliver only the archives named by the current
manifest plus that manifest. Regenerate after screenshots/source/report changes.
