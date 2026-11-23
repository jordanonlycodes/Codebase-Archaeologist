#!/usr/bin/env python3
"""Install only the checksum-pinned project model. No deserialization/network/training."""
from pathlib import Path
import argparse,hashlib,json,shutil,tempfile
ROOT=Path(__file__).resolve().parents[1]
APPROVED='9988945c6c851e885f3942a406a4d6c7d704547797e266d6d0aed95520db74e6'
NAMES=('pipeline.joblib','metadata.json','feature_schema.json')
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def install(source=None,destination=None):
    source=Path(source or ROOT/'models/devign-v1');destination=Path(destination or ROOT/'artifacts/devign-v1')
    manifest=json.loads((source/'manifest.json').read_text())
    if set(manifest['files'])!=set(NAMES) or manifest['files']['pipeline.joblib']['sha256']!=APPROVED:
        raise ValueError('Not the approved project model manifest')
    for name in NAMES:
        path=source/name;record=manifest['files'][name]
        if not path.is_file() or path.is_symlink() or digest(path)!=record['sha256'] or path.stat().st_size!=record['bytes']:
            raise ValueError('Packaged model integrity failure: '+name)
        if (destination/name).exists() and digest(destination/name)!=record['sha256']:
            raise ValueError('Refusing to overwrite a different existing artifact: '+name)
    destination.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.model-install-',dir=destination.parent) as temporary:
        for name in NAMES:shutil.copyfile(source/name,Path(temporary)/name)
        for name in NAMES:
            if not (destination/name).exists():(Path(temporary)/name).replace(destination/name)
    return {'model_version':manifest['model_version'],'sha256':APPROVED,'files_verified':len(NAMES),'network':False,'training':False}
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--destination',type=Path)
    args=p.parse_args();print(json.dumps(install(destination=args.destination),indent=2))
