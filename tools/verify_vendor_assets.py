#!/usr/bin/env python3
"""Verify the reviewed offline distribution and retained notice evidence."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
BUNDLE='19b3be27040fc894e56d684d53c5f62526c25e5d27f37e8fe91fafff605e4ef4'
COMMIT='9806444ee2af34a0a45ecc8ea035ec9efa929d54'
def inspect(directory=None):
    directory=Path(directory or ROOT/'app/static/vendor');receipt=directory/'graph-assets.json'
    result={'local_bundle_available':False,'redistribution_approved':False}
    if not receipt.exists():return {**result,'reason':'Optional3D is not installed;2D remains available.'}
    try:
        r=json.loads(receipt.read_text());bundle=directory/'3d-force-graph-1.73.3.min.js';license_file=directory/'3d-force-graph-1.73.3.LICENSE'
        digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
        result.update(local_bundle_available=bundle.is_file(),bundle_matches_receipt=bundle.is_file() and digest(bundle)==r.get('bundle_sha256'),version=r.get('version'))
        approved=(r.get('package_sha256')=='520998cc26902fa8c74496adcc314b19a50cfb267174ab313407642958e7ecef' and r.get('upstream_commit')==COMMIT and r.get('bundle_sha256')==BUNDLE and result['bundle_matches_receipt'] and license_file.is_file() and digest(license_file)==r.get('license_sha256') and len(r.get('evidence',{}))==3)
        for name,sha in r.get('evidence',{}).items():
            p=(ROOT/name).resolve()
            approved=approved and p.is_relative_to(ROOT/'third_party/graph') and p.is_file() and digest(p)==sha
        result.update(redistribution_approved=bool(approved),reason='Reviewed published distribution and conservative runtime/helper notices match.' if approved else 'Unverified/tampered evidence; do not redistribute.')
    except (OSError,ValueError,KeyError):result['reason']='Invalid or missing graph evidence; do not redistribute.'
    return result
if __name__=='__main__':print(json.dumps(inspect(),indent=2))
