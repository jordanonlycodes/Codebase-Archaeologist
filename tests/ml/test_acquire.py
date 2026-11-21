import json

import pytest

from app.ml.acquire import acquire, verify_manifest, DATASET
from app.ml.io import digest, write_json


def cached_manifest(root):
    # Dummy bytes test checksum/path mechanics only; never parsed or used to train.
    names = [f"{split}-00000-of-00001.parquet" for split in ("train", "validation", "test")]
    for name in names:
        (root / name).write_bytes(b"checksum fixture, not a dataset")
    manifest = {"dataset": DATASET, "license": "c-uda",
                "splits": {name.split("-")[0]: [name] for name in names},
                "files": [{"local": name, "sha256": digest(root / name)} for name in names]}
    write_json(root / "manifest.json", manifest)
    return manifest


def test_verified_cache_avoids_downloads(tmp_path, monkeypatch):
    manifest = cached_manifest(tmp_path)
    monkeypatch.setattr("app.ml.acquire.fetch", lambda *a, **kw: pytest.fail("Cache should be reused offline"))
    assert acquire(tmp_path) == manifest


def test_corrupt_cached_data_rejected(tmp_path):
    cached_manifest(tmp_path)
    (tmp_path / "train-00000-of-00001.parquet").write_bytes(b"modified")
    with pytest.raises(ValueError, match="modified"):
        verify_manifest(tmp_path)


def test_manifest_cannot_reference_unverified_external_data(tmp_path):
    manifest = cached_manifest(tmp_path)
    manifest["splits"]["test"] = ["../outside.parquet"]
    write_json(tmp_path / "manifest.json", manifest)
    with pytest.raises(ValueError, match="checksummed"):
        verify_manifest(tmp_path)


def test_download_failure_does_not_create_complete_manifest(tmp_path, monkeypatch):
    def fail(*args, **kwargs):
        raise OSError("network unavailable")
    monkeypatch.setattr("app.ml.acquire.fetch", fail)
    with pytest.raises(OSError, match="network unavailable"):
        acquire(tmp_path)
    assert not (tmp_path / "manifest.json").exists()


def test_pinned_plan_checksum_cannot_be_replaced(tmp_path, monkeypatch):
    plan = {"files": [{"local": "DATASET_CARD.md", "url": "https://example.invalid/pinned", "sha256": "0" * 64}]}
    write_json(tmp_path / "download_plan.json", plan)
    def replacement(url, path, *args):
        path.write_bytes(b"changed upstream bytes")
    monkeypatch.setattr("app.ml.acquire.fetch", replacement)
    with pytest.raises(ValueError, match="checksum mismatch"):
        acquire(tmp_path)
    assert not (tmp_path / "manifest.json").exists()
