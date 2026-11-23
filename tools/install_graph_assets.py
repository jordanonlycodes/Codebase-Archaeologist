#!/usr/bin/env python3
"""Install pinned 3D browser bundle and package license; no npm/build step required.

Only this explicit developer command uses the network. The running application uses
local files exclusively and never downloads scripts or sends repository data out.
"""
from io import BytesIO
from pathlib import Path
import hashlib
import json
import tarfile
from urllib.request import urlopen

VERSION = '1.73.3'
URL = f'https://registry.npmjs.org/3d-force-graph/-/3d-force-graph-{VERSION}.tgz'
DESTINATION = Path(__file__).resolve().parents[1] / 'app/static/vendor'
MAXIMUM = 12 * 1024 * 1024


def install():
    with urlopen(URL, timeout=30) as response:
        data = response.read(MAXIMUM + 1)
    if len(data) > MAXIMUM:
        raise ValueError('Pinned package exceeds the download limit.')
    with tarfile.open(fileobj=BytesIO(data), mode='r:gz') as archive:
        def member(name):
            record = archive.getmember('package/' + name)
            if not record.isfile() or record.size > MAXIMUM:
                raise ValueError('Unexpected package member.')
            return archive.extractfile(record).read()
        package = json.loads(member('package.json'))
        if package['name'] != '3d-force-graph' or package['version'] != VERSION:
            raise ValueError('Unexpected package identity.')
        bundle = member('dist/3d-force-graph.min.js')
        license_text = member('LICENSE')
    DESTINATION.mkdir(parents=True, exist_ok=True)
    # Nothing is written until the complete package has been checked. No extractall.
    (DESTINATION / f'3d-force-graph-{VERSION}.min.js').write_bytes(bundle)
    (DESTINATION / f'3d-force-graph-{VERSION}.LICENSE').write_bytes(license_text)
    receipt = {'package': package['name'], 'version': VERSION, 'source': URL,
               'package_sha256': hashlib.sha256(data).hexdigest(),
               'bundle_sha256': hashlib.sha256(bundle).hexdigest(),
               'bundled_dependencies': package.get('dependencies', {})}
    previous=DESTINATION/'graph-assets.json'
    # Retain independently reviewed closure only for the identical published bytes.
    if previous.is_file():
        old=json.loads(previous.read_text())
        if old.get('bundle_sha256')==receipt['bundle_sha256'] and old.get('package_sha256')==receipt['package_sha256']:
            for key in ['upstream_commit','provenance','evidence','license_sha256']:
                if key in old:receipt[key]=old[key]
    previous.write_text(json.dumps(receipt, indent=2) + '\n')
    print(f'Installed local 3D bundle {VERSION}; reload the dashboard. Receipt: {DESTINATION / "graph-assets.json"}')


if __name__ == '__main__':
    try:
        install()
    except (OSError, ValueError, KeyError, tarfile.TarError) as error:
        raise SystemExit(f'3D asset installation failed: {error}. No CDN fallback is used.')
