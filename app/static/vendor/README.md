# Local graph assets

The dependency-free 2D adapter works without vendor assets.

The real 3D adapter expects `3d-force-graph-1.73.3.min.js`, the upstream UMD bundle
including Three.js and its force/orbit controls. Run from the project root:

```bash
python tools/install_graph_assets.py
```

This downloads the **exact** npm package archive over HTTPS, reads only its named
bundle, LICENSE and package.json (no package installation scripts), and retains the
upstream MIT license and a SHA-256 receipt. The package's bundled dependency declarations
are recorded in `graph-assets.json`; preserve upstream license comments in the bundle.
See https://github.com/vasturiano/3d-force-graph/tree/v1.73.3 and its LICENSE
(Copyright 2017 Vasco Asturiano); Three.js is MIT licensed, https://threejs.org/.

A fresh checkout may omit these locally installed files. When the bundle is absent,
the 3D switch reports it and falls back to analytical 2D. A locally present bundle is
not proof of independently verified upstream provenance: compare the archive/receipt
and check bundled dependency attribution before redistribution. The currently audited
minified bundle has no embedded license notices, so its top-level MIT license alone
does not establish that every bundled dependency notice has been retained. See
[the Task7A vendor assessment](../../../docs/task7a_university_compliance_audit.md).
The application never requests a CDN. Do not strip license notices from installed assets.
The built bundle freezes its included code; no runtime semver dependency resolution
occurs. The download receipt is a provenance record, not an independent authenticity
signature. Review the package/receipt before distributing locally installed assets.
