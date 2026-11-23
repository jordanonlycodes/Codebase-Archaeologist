# Task7D — graph vendor provenance decision

Observed local file:app/static/vendor/3d-force-graph-1.73.3.min.js,691294bytes,
SHA19b3be27040fc894e56d684d53c5f62526c25e5d27f37e8fe91fafff605e4ef4.
The existing unsigned receipt names the fixed npm tarball and archive SHA
520998cc26902fa8c74496adcc314b19a50cfb267174ab313407642958e7ecef.
Local bundle digest agrees; no archive exists locally for byte comparison. Fresh direct
npm fetch fails Temporary failure in name resolution. Web retrieval independently
confirms the version-tagged top-level MIT text/copyright, matching the local license.
This does NOT prove the minified bytes or complete transitive notices are cleared.

3D adapter lazily loads this local bundle;2D remains available without it. The running
app never downloads CDN scripts. Existing source installer downloads from the official
fixed npm URL, extracts named bounded package members and writes a receipt/license. It
has no resolved transitive lock/SBOM. Recorded dependency ranges include three>=.118<1,
three-forcegraph1,three-render-objects^1.29,kapsule1,accessor-fn1. No embedded copyright/
license comment was found in the minified file. Guessing all resolved versions/license
texts from ranges would be inappropriate.

Decision:preserve all three existing untracked files; do NOT redistribute them yet.
Source/submission builder explicitly excludes app/static/vendor assets. Top-level MIT
alone is insufficient to claim closure. THIRD_PARTY_NOTICES.md explains the boundary.
This is a release blocker for portable OFFLINE3D, not a reason to replace the graph engine
or disable the existing local installed copy. Graph harness still verifies its adapter,
controls and truthful missing-asset fallback; it is not a rendered WebGL test.

Next exact action on a networked machine:download the pinned npm1.73.3archive; verify its
SHA against receipt; compare dist bundle/LICENSE bytes; inspect tag build/lock and resolved
bundled imports; preserve required transitive licenses with exact versions; record source
URLs/digests. Only then make an authorized vendor commit. Alternatively demonstrate2D
and explicitly mark3D unavailable. Do not claim successful offline3D from a CDN.
