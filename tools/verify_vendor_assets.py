#!/usr/bin/env python3
"""Report local receipt agreement; intentionally NOT a redistribution certificate."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
def inspect(directory=None):
    directory=Path(directory or ROOT/'app/static/vendor');receipt=directory/'graph-assets.json'
    if not receipt.exists():return {'local_bundle_available':False,'redistribution_approved':False,'reason':'Optional3D is not installed;2D remains available.'}
    record=json.loads(receipt.read_text());bundle=directory/'3d-force-graph-1.73.3.min.js'
    return {'local_bundle_available':bundle.is_file(),'bundle_matches_receipt':bundle.is_file() and hashlib.sha256(bundle.read_bytes()).hexdigest()==record.get('bundle_sha256'),
            'version':record.get('version'),'redistribution_approved':False,'reason':'Archive/transitive provenance not independently verified; keep untracked and excluded.'}
if __name__=='__main__':print(json.dumps(inspect(),indent=2))
