# Task7D — submission candidate manifest

Generator:`python tools/build_submission.py`. Output directory:submission/final/.
Status is explicitly **PARTIAL — SUBMISSION CANDIDATE**, never unconditional FINAL.

Deliver both archives plus manifest.json:

- Codebase_Archaeologist_Submission_Candidate.zip:Word/PDF,confirmed academic identities,
  setup/demo guides,verification record,approved exact model/schema/metadata/manifest,
  provider/font notices and a per-file SHA/size manifest.
- source.zip:clean committed source fallback while GitHub publication is pending; no
  .git,.venv,data/artifacts caches,secrets,ZIP recursion or unapproved graph vendor assets.
  Contains only approved production model binary,not experimental checkpoints.
- manifest.json:source commit,generation date,authors,archive sizes/SHA-256,payload hashes,
  CRC/extracted-payload verification and exact remaining actions. It does not self-hash.

The generated payload directory and ZIPs are not committed redundantly. Small outer
README/manifest are tracked. Source archive reads committed Git objects,not arbitrary
untracked files. Academic report/model copies are deliberate standalone evaluator
conveniences; the source ZIP is separate rather than nested duplicate full repository.
No unknown leftover payload file is silently shipped. Rebuilding replaces only known
own-generated files and receipts; other user files trigger a stop,not deletion.

Builder bounds:20MiB/member,80MiB aggregate; safe normalized relative paths; no links;
only exactapproved model hash; copies license notices; no credential collection. ZIPCRC
and extracted payload hashes are verified. Exact final archive sizes/digests come from
submission/final/manifest.json,not manually invented static values here.

Outstanding:real screenshots/Office/browser/demo acceptance,portable offline3D notices,
remote publication,and instructor interpretation of final-test-for-all-candidates wording.
Academic metadata is no longer missing. Any later screenshot/report/source change needs
regeneration/validation and a NEW package/manifest; do not reuse stale checksums.
