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

## Optional 3D browser bundle — redistribution unresolved

3d-force-graph1.73.3 top-level MIT license is verified at the upstream version tag:
https://raw.githubusercontent.com/vasturiano/3d-force-graph/v1.73.3/LICENSE
Copyright(c)2017Vasco Asturiano. Existing local bundle/receipt/license remain untouched
and UNTRACKED. The local bundle's SHA matches its receipt, but that is not independent
verification of its upstream archive or complete bundled-license closure. The recorded
package depends on accessor-fn,kapsule,three,three-forcegraph,three-render-objects using
ranges; actual resolved transitive versions/notices are not recorded. No license headers
were found in the minified bundle. npm retrieval currently fails DNS.

Therefore this release does NOT redistribute those three files in Git/source/submission
archives. Existing developer-local3D remains intact, and2D fallback is preserved. Explicit
upstream installation is available via tools/install_graph_assets.py; that command is a
network operation and does not itself constitute transitive-license approval. An offline
clean checkout is NOT claimed to include working3D until provenance/notices are resolved.
Do not silently pull scripts from a public CDN at application runtime.
