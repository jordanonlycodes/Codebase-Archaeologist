import io
import zipfile

import pytest


@pytest.fixture
def make_zip():
    def build(files, compression=zipfile.ZIP_STORED):
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, "w", compression=compression) as archive:
            for name, content in files.items():
                archive.writestr(name, content)
        stream.seek(0)
        return stream
    return build


@pytest.fixture
def sample_files():
    return {
        "repo/src/main.py": '# heading\n\nx = 1  # inline\nprint(x)\n',
        "repo/src/app.js": '// unavailable comment metric\nconst x = 1;\n',
        "repo/README.md": '# Example\n\nReal repository.\n',
        "repo/config.json": '{"enabled": true}\n',
        "repo/.git/config": 'ignored',
        "repo/node_modules/lib/index.js": 'ignored',
        "repo/assets/logo.png": b'\x89PNG\x00',
        "repo/assets/binary.dat": b'\x00\x01\x02',
        "repo/empty/": '',
    }
