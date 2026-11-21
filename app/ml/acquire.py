"""Download official split Parquet files without executing dataset scripts.

Usage: python -m app.ml.acquire
No optional ML libraries are needed for download. A completed manifest is reused
offline only after verifying every local checksum.
"""

import argparse
import json
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from app.ml.io import digest, read_json, write_json

DATASET = "google/code_x_glue_cc_defect_detection"
SOURCE = f"https://huggingface.co/datasets/{DATASET}"
LICENSE_URL = "https://raw.githubusercontent.com/microsoft/Computational-Use-of-Data-Agreement/master/C-UDA-1.0.md"
DEFAULT_RAW = Path("data/raw/devign")
EXPECTED_SIZES = {"train": 21854, "validation": 2732, "test": 2732}
REQUIRED_SCHEMA = {"id": "int32", "func": "string", "target": "bool", "project": "string", "commit_id": "string"}


def fetch(url: str, destination: Path, max_bytes: int = 100 * 1024 * 1024) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".part")
    request = urllib.request.Request(url, headers={"User-Agent": "CodebaseArchaeologist/0.2"})
    try:
        with urllib.request.urlopen(request, timeout=60) as response, temporary.open("wb") as output:
            count = 0
            while chunk := response.read(1024 * 1024):
                count += len(chunk)
                if count > max_bytes:
                    raise ValueError(f"Download exceeds size limit: {url}")
                output.write(chunk)
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)


def verify_manifest(root: Path) -> dict:
    manifest = read_json(root / "manifest.json")
    if manifest.get("dataset") != DATASET or manifest.get("license") != "c-uda":
        raise ValueError("Unexpected dataset identity or declared license")
    if set(manifest.get("splits", {})) != set(EXPECTED_SIZES):
        raise ValueError("All three official splits must be present")
    recorded = {spec["local"] for spec in manifest["files"]}
    for split, filenames in manifest["splits"].items():
        if not filenames or any(name not in recorded or not re.fullmatch(rf"{split}-\d+-of-\d+\.parquet", name) for name in filenames):
            raise ValueError("Manifest split files must be checksummed official Parquet paths")
    for spec in manifest["files"]:
        name = spec["local"]
        if Path(name).name != name:
            raise ValueError("Manifest contains an unsafe local path")
        path = root / name
        if not path.is_file() or digest(path) != spec["sha256"]:
            raise ValueError(f"Missing or modified source file: {name}; acquire again in a fresh data directory")
    return manifest


def acquire(root: Path = DEFAULT_RAW) -> dict:
    if (root / "manifest.json").exists():
        return verify_manifest(root)
    root.mkdir(parents=True, exist_ok=True)
    plan_path = root / "download_plan.json"
    if plan_path.exists():
        plan = read_json(plan_path)
    else:
        api_path = root / "huggingface_metadata.json"
        fetch(f"https://huggingface.co/api/datasets/{DATASET}?blobs=true", api_path, 2 * 1024 * 1024)
        metadata = read_json(api_path)
        revision = metadata["sha"]
        if not re.fullmatch(r"[a-f0-9]{40}", revision):
            raise ValueError("Dataset API did not return an immutable revision")
        declared = metadata.get("cardData", {}).get("license")
        if declared != "c-uda" and declared != ["c-uda"]:
            raise ValueError(f"Dataset license changed or is missing: {declared!r}; review before processing")
        files = []
        splits = {name: [] for name in EXPECTED_SIZES}
        for sibling in metadata["siblings"]:
            name = sibling["rfilename"]
            match = re.fullmatch(r"data/(train|validation|test)-\d+-of-\d+\.parquet", name)
            if match:
                local = name.split("/")[-1]
                spec = {"url": f"{SOURCE}/resolve/{revision}/{name}", "local": local}
                lfs = sibling.get("lfs") or {}
                expected_hash = lfs.get("sha256") or lfs.get("oid")
                if expected_hash:
                    spec["expected_sha256"] = expected_hash.removeprefix("sha256:")
                files.append(spec)
                splits[match[1]].append(local)
        if any(not values for values in splits.values()):
            raise ValueError("Official train/validation/test Parquet files were not found")
        files.extend([
            {"local": "DATASET_CARD.md", "url": f"{SOURCE}/resolve/{revision}/README.md"},
            {"local": "C-UDA-1.0.md", "url": LICENSE_URL},
        ])
        plan = {"dataset": DATASET, "source": SOURCE, "revision": revision, "license": "c-uda",
                "license_url": LICENSE_URL, "expected_sizes": EXPECTED_SIZES,
                "expected_schema": REQUIRED_SCHEMA, "splits": splits, "files": files}
        write_json(plan_path, plan)
    for spec in plan["files"]:
        path = root / spec["local"]
        expected = spec.get("sha256") or spec.get("expected_sha256")
        if not path.exists() or not expected or digest(path) != expected:
            print(f"Downloading {spec['local']}", flush=True)
            fetch(spec["url"], path)
        actual = digest(path)
        if expected and actual != expected:
            raise ValueError(f"Source checksum mismatch: {spec['local']}")
        spec["sha256"] = actual
        spec["bytes"] = path.stat().st_size
        write_json(plan_path, plan)
    # Preserve the provider declaration as well as the license text before data processing.
    if "c-uda" not in (root / "DATASET_CARD.md").read_text(encoding="utf-8").lower():
        raise ValueError("Downloaded dataset card does not declare C-UDA")
    plan["acquired_at"] = datetime.now(timezone.utc).isoformat()
    write_json(root / "manifest.json", plan)
    return verify_manifest(root)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW)
    args = parser.parse_args()
    try:
        manifest = acquire(args.raw_dir)
    except (OSError, ValueError, KeyError) as exc:
        write_json(args.raw_dir / "acquisition_status.json", {"status": "blocked", "error": str(exc), "source": SOURCE})
        parser.exit(1, f"Acquisition blocked: {exc}\nNo replacement or generated data was created.\n")
    write_json(args.raw_dir / "acquisition_status.json", {"status": "complete", "revision": manifest["revision"]})
    print(json.dumps({"status": "complete", "revision": manifest["revision"], "directory": str(args.raw_dir)}))


if __name__ == "__main__":
    main()
