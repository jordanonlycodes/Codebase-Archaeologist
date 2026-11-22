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
