# Task 6B — recovery and implementation record

## A complete — audit and contracts

Baseline: 440 Python tests passed, zero failed/skipped; existing frontend runners included.
Working tree initially had only the three user-owned untracked 3D vendor assets. Main
was synchronized at 2445e90. Preserve those assets, ML, reports and provider configuration.

GitHub ingestion downloads a verified pinned ZIP, not Git history; extraction excludes
.git and removes source after analysis. Browser analysis is per-tab IndexedDB, two-hour
TTL, 24 MiB/row, three snapshots, with no server-global repository store.

Design: explicit bounded public GitHub REST history retrieval from that exact snapshot
SHA. No network Git clone, hooks, filters or submodules. Fixed api.github.com requests,
no redirects/proxies/credentials, byte/request/deadline bounds. Operator/test-only local
Git reader (never a filesystem API) supplies genuine fixture evidence through the same
normalization/comparison core. Exact tree-to-tree comparison handles divergent revisions;
rename recognition is unique identical-blob matching, not speculative similarity.
History metadata persists inside the original snapshot without extending TTL or changing
its ID. Source patches are transient only. ZIP archives never manufacture history.

Next: B real commits/churn/activity and fixtures; C exact revision/tree comparisons;
D workspace/state; E timeline/activity; F churn/comparison; G evolution; H stable-ID
links; I full tests, visual attempt, documentation and safe push. Each tested stage commits.

## B complete — authentic history core

Added typed commit/change/tree contracts, fixed-host public REST reader, bounded read-only
operator/test Git adapter, parent/date preservation, deterministic churn and UTC activity.
History packets strip all patches. Missing shallow parents remain explicitly incomplete;
no fake initial additions. 16 genuine-fixture/network checks passed (9 seconds), covering
branches, merges, authors, timezones, renames, deletions, binary/unusual files, hooks,
detached/shallow histories, limits and reproducibility. The sandbox selector workaround
was needed for threaded Git reads; no application workaround was added.
Default 24 commits balances REST fanout; file measurements are explicitly bounded.
Next: C typed public history/tree/comparison API, request boundary and additional tests.

## C complete — comparison/tree API and boundaries

Added /api/history/load, /tree and /compare with explicit full-SHA URL/anchor contracts.
Revisions must be in the pinned ancestor window. Exact tree comparison works for divergent
revisions, unique identical-blob renames, text/binary/large-file gaps and bounded patches;
incomplete trees cannot imply deletions. No source patch is stored in history.
Shared admission bounds two repository operations, 4 KiB history requests and 10s upload
read time. 24 history tests passed, including genuine two-direction/divergent comparisons,
API contracts, no public filesystem paths, SSRF rejection and serialization bounds.
Next D: per-snapshot bounded persistence and dedicated source-aware workspace.

## D complete — workspace and continuity

Added /workspace/time-machine, dedicated lazy assets and shared navigation/lifecycle.
Public-source retrieval is explicit; ZIPs show an intentional no-history state without
network or fake plots. Loaded commits have real inspection and filtering. History metadata
is bounded to 2 MiB within the existing row, retaining the exact snapshot ID and expiry;
replacement/expiry/identity mismatches cannot attach another repository's history.
19 product Python checks passed, including real Git-fixture history fetch/reload cases;
16 store cases passed. Current analysis and JSON export remain available. Next E replaces
the initial working commit exploration with the interactive timeline/activity canvas.
