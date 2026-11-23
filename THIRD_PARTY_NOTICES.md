# Third-party notices and release boundaries

No project-wide software LICENSE has been selected in this repository. Do not infer a
new MIT license for the application from a dependency's MIT notice or GitHub visibility.
Academic publication/submission here does not grant blanket third-party source rights.

## Locally served fonts

Noto Sans/Noto Serif Display subsets and outlined brand wordmarks use the local SIL
Open Font License notice at app/static/product/fonts/OFL.txt (Noto Project Authors2022).
That file is retained in source distributions. No proprietary font is newly introduced.
Report PDFs embed DejaVu subsets from the existing Matplotlib installation; corresponding
font permission/copyright text is preserved in third_party/DejaVu-LICENSE.txt. Other
Python dependency licenses remain in their installed distributions; runtime wheels are
not republished in the submission archive.

## Production model / dataset

models/devign-v1 contains the exact approved numeric-feature Random Forest and original
metadata/schema. Model/provider attribution and the copied C-UDA agreement are included
there. C-UDA2.2/5.5 discusses trained-model Results without more than de minimis source;
no raw training functions or other candidate binaries are distributed. See the model
portability document for the inspected basis and limits. This is not blanket clearance
for FFmpeg/QEMU source reuse or a new license over project-authored work.

## Offline 3D distribution — verified Task7E

3d-force-graph1.73.3 is MIT, Copyright(c)2017 Vasco Asturiano. The published npm
archive was independently fetched and its bundle/LICENSE bytes match the local files.
Upstream gitHead9806444ee2af34a0a45ecc8ea035ec9efa929d54 supplies the Yarn lock.
Its33 runtime dependency packages plus2 explicit Babel build/helper packages have
integrity-checked npm archives; all collected license declarations/texts are MIT, ISC or
BSD-3-Clause. Conservative notices include runtime modules even if tree-shaken away.

Retain app/static/vendor/3d-force-graph-1.73.3.LICENSE and third_party/graph/LICENSES.txt.
third_party/graph/provenance.json records exact versions, source URLs and digests;
upstream-yarn.lock preserves the primary source lock. This verifies redistribution
notices and published artifact identity, not a bit-for-bit rebuild or trademark clearance.
The running app serves local assets only; no runtime CDN or package scripts are involved.
Recovery: tools/resolve_graph_provenance.py; integrity: tools/verify_vendor_assets.py.
See docs/task7e_3d_asset_resolution.md for the complete evidence and limitations.
