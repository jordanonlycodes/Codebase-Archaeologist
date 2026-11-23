# Task7E offline 3D asset resolution

Published npm 3d-force-graph1.73.3 archive was fetched from its fixed registry destination.
SHA256520998cc26902fa8c74496adcc314b19a50cfb267174ab313407642958e7ecef;
bundle SHA25619b3be27040fc894e56d684d53c5f62526c25e5d27f37e8fe91fafff605e4ef4.
Both bundle and MIT LICENSE match the three original local vendor files byte-for-byte.
No replacement library or runtime CDN is introduced.

Registry gitHead9806444ee2af34a0a45ecc8ea035ec9efa929d54 identifies upstream source.
Its actual yarn.lock resolves33runtime packages. Every runtime npm archive was fetched
from registry.npmjs.org and verified against the lock's integrity before extracting only
root license/notice files. Two explicit Babel build/helper packages are conservatively
included in addition; @babel/runtime already belongs to runtime closure.35total records,
all MIT/ISC/BSD-3-Clause. Each copyright/permission text is retained, not guessed from names.

Evidence:third_party/graph/upstream-yarn.lock,provenance.json,LICENSES.txt. Recovery script
is tools/resolve_graph_provenance.py; checksums in graph-assets.json bind evidence files.
tools/verify_vendor_assets.py fails closed on missing or changed bundle/evidence. This is
review of published-artifact identity and conservative license closure, not bit-identical
source build reproduction or a legal certification. Upstream ranges are not used as exact
versions; actual release lock and archive integrity are retained.

The exact three vendor files are now authorized for tracking. Source packaging has a
separate reviewed allowlist: default unreviewed vendor exclusion remains tested. It checks
committed bytes match reviewed working evidence. Payload carries bundle,root MIT and
all notices/lock/provenance. Chromium actually rendered local ThreeGraph without network
script loading; pan/orbit/zoom/reset changed measured camera state. Headless GPU reported
software-WebGL/performance warnings; hardware FPS is not claimed.
