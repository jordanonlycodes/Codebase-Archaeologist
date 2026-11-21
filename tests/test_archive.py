import io
import stat
import struct
import zipfile
from dataclasses import replace

import pytest

from app.config import LIMITS
from app.errors import AnalysisError
from app.ingestion.archive import extract_repository


@pytest.mark.parametrize("name", ["../escape.py", "/tmp/escape.py", "repo/../../escape.py", "C:/escape.py",
                                 "repo\\..\\escape.py", "repo//main.py", "./main.py", "repo/./main.py",
                                 "repo/evil\nname.py", "repo/file.py:stream"])
def test_unsafe_paths_are_rejected(make_zip, tmp_path, name):
    with pytest.raises(AnalysisError) as error:
        extract_repository(make_zip({name: "x=1"}), tmp_path)
    assert error.value.code == "unsafe_archive"
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("kind", [stat.S_IFLNK, stat.S_IFIFO, stat.S_IFSOCK, stat.S_IFCHR, stat.S_IFBLK])
def test_links_and_special_files_rejected(make_zip, tmp_path, kind):
    info = zipfile.ZipInfo("repo/.git/unsafe")  # Even excluded paths are validated.
    info.create_system = 3
    info.external_attr = (kind | 0o777) << 16
    with pytest.raises(AnalysisError, match="Links and special"):
        extract_repository(make_zip({info: "/etc/passwd"}), tmp_path)


@pytest.mark.parametrize("files", [
    {"main.py": "a", "MAIN.py": "b"},
    {"src": "a", "src/main.py": "b"},
    {"src/main.py": "b", "src": "a"},
])
def test_conflicting_paths(make_zip, tmp_path, files):
    with pytest.raises(AnalysisError):
        extract_repository(make_zip(files), tmp_path)
    assert not list(tmp_path.iterdir())


def test_duplicate_entry(make_zip, tmp_path):
    stream = make_zip({"main.py": "one"})
    with pytest.warns(UserWarning), zipfile.ZipFile(stream, "a") as archive:
        archive.writestr("main.py", "two")
    with pytest.raises(AnalysisError, match="Duplicate"):
        extract_repository(stream, tmp_path)


@pytest.mark.parametrize("data", [b"", b"not a zip", b"PK\x03\x04broken"])
def test_invalid_zip(tmp_path, data):
    with pytest.raises(AnalysisError):
        extract_repository(io.BytesIO(data), tmp_path)


def test_empty_archive(make_zip, tmp_path):
    with pytest.raises(AnalysisError) as error:
        extract_repository(make_zip({}), tmp_path)
    assert error.value.code == "empty_repository"


@pytest.mark.parametrize("limit,files", [
    ({"upload_bytes": 20}, {"main.py": "a"}),
    ({"entries": 1}, {"a.py": "a", "b.py": "b"}),
    ({"file_bytes": 3}, {"main.py": "1234"}),
    ({"expanded_bytes": 5}, {"a.py": "123", "b.py": "456"}),
    ({"depth": 2}, {"a/b/c.py": "a"}),
    ({"path_bytes": 5}, {"long-name.py": "a"}),
])
def test_archive_limits(make_zip, tmp_path, limit, files):
    with pytest.raises(AnalysisError) as error:
        extract_repository(make_zip(files), tmp_path, replace(LIMITS, **limit))
    assert error.value.status == 413
    assert not list(tmp_path.iterdir())


def test_compression_bomb(make_zip, tmp_path):
    with pytest.raises(AnalysisError, match="compression ratio"):
        extract_repository(make_zip({"big.py": "a" * 100000}, zipfile.ZIP_DEFLATED), tmp_path)


def test_unsupported_compression(make_zip, tmp_path):
    with pytest.raises(AnalysisError, match="stored or deflate"):
        extract_repository(make_zip({"main.py": "x=1"}, zipfile.ZIP_BZIP2), tmp_path)


def test_encryption_flag_rejected(make_zip, tmp_path):
    data = bytearray(make_zip({"main.py": "x=1"}).getvalue())
    central = data.index(b"PK\x01\x02")
    struct.pack_into("<H", data, central + 8, 1)
    with pytest.raises(AnalysisError, match="Encrypted"):
        extract_repository(io.BytesIO(data), tmp_path)


def test_crc_corruption(make_zip, tmp_path):
    data = make_zip({"main.py": "x=1"}).getvalue().replace(b"x=1", b"x=2")
    with pytest.raises(AnalysisError, match="corrupt"):
        extract_repository(io.BytesIO(data), tmp_path)


def test_forged_central_count(make_zip, tmp_path):
    data = bytearray(make_zip({"a.py": "1", "b.py": "2"}).getvalue())
    end = data.rfind(b"PK\x05\x06")
    struct.pack_into("<HH", data, end + 8, 1, 1)
    with pytest.raises(AnalysisError):
        extract_repository(io.BytesIO(data), tmp_path, replace(LIMITS, entries=1))


def test_nul_in_filename(make_zip, tmp_path):
    data = make_zip({"evilXname.py": "x=1"}).getvalue().replace(b"evilXname", b"evil\x00name")
    with pytest.raises(AnalysisError, match="unsafe path"):
        extract_repository(io.BytesIO(data), tmp_path)


def test_exclusions_and_normal_extraction(make_zip, sample_files, tmp_path):
    result = extract_repository(make_zip(sample_files, zipfile.ZIP_DEFLATED), tmp_path)
    assert result == {"archive_entries": 9, "skipped": {"excluded_directory": 2, "binary_or_archive": 1}}
    assert (tmp_path / "repo/src/main.py").read_text() == sample_files["repo/src/main.py"]
    assert not (tmp_path / "repo/.git").exists()
    assert not (tmp_path / "repo/node_modules").exists()
    assert not (tmp_path / "repo/assets/logo.png").exists()


def test_custom_virtual_environment(make_zip, tmp_path):
    extract_repository(make_zip({"custom/pyvenv.cfg": "home=/usr", "custom/lib/a.py": "ignored", "app.py": "x=1"}), tmp_path)
    assert not (tmp_path / "custom").exists()
    assert (tmp_path / "app.py").exists()


def test_archive_code_is_never_executed(make_zip, tmp_path):
    marker = tmp_path.parent / f"{tmp_path.name}-executed"
    code = f"from pathlib import Path\nPath({str(marker)!r}).touch()\n"
    extract_repository(make_zip({"setup.py": code, "sitecustomize.py": code}), tmp_path)
    assert not marker.exists()
