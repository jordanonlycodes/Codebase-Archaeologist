"""Official split loading and explicit development-only cleaning.

Test labels are loaded only in the final evaluation phase. Test source hashes
are permitted solely for contamination removal and structural integrity checks.
"""

import hashlib
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

from app.ml.acquire import EXPECTED_SIZES, REQUIRED_SCHEMA, verify_manifest
from app.ml.features import normalize_source

POLICY_VERSION = "devign-clean-v1"
FIELDS = tuple(REQUIRED_SCHEMA)


def fingerprint(source) -> str | None:
    if not isinstance(source, str) or not source.strip():
        return None
    return hashlib.sha256(normalize_source(source).encode("utf-8")).hexdigest()


def valid_label(label) -> bool:
    return isinstance(label, (bool, int)) and label in (0, 1)


def load_split(root: Path, split: str, *, include_target: bool = True) -> list[dict]:
    import pyarrow.parquet as pq
    manifest = verify_manifest(root)
    if split not in EXPECTED_SIZES:
        raise ValueError("Unknown official split")
    records = []
    for filename in sorted(manifest["splits"][split]):
        parquet = pq.ParquetFile(root / filename)
        actual = {field.name: str(field.type) for field in parquet.schema_arrow}
        if actual != REQUIRED_SCHEMA:
            raise ValueError(f"Unexpected actual Parquet schema for {filename}: {actual}")
        columns = list(FIELDS if include_target else (name for name in FIELDS if name != "target"))
        records.extend(parquet.read(columns=columns).to_pylist())
    if len(records) != EXPECTED_SIZES[split]:
        raise ValueError(f"Unexpected official {split} size: {len(records)}")
    return records


def _groups(rows):
    groups = defaultdict(list)
    for index, row in enumerate(rows):
        key = fingerprint(row.get("func"))
        if key:
            groups[key].append(index)
    return groups


def split_audit(rows, *, labels_available=True):
    groups = _groups(rows)
    raw = Counter(row["func"] for row in rows if isinstance(row.get("func"), str))
    missing = {field: sum(row.get(field) is None or (isinstance(row.get(field), str) and not row[field].strip()) for row in rows)
               for field in FIELDS if labels_available or field != "target"}
    conflicts = []
    if labels_available:
        conflicts = [key for key, indexes in groups.items()
                     if len({int(rows[index]["target"]) for index in indexes if valid_label(rows[index].get("target"))}) > 1]
    return {
        "rows": len(rows), "missing": missing,
        "labels": dict(sorted(Counter(str(int(row["target"])) for row in rows if valid_label(row.get("target"))).items())) if labels_available else None,
        "invalid_labels": sum(not valid_label(row.get("target")) for row in rows) if labels_available else None,
        "exact_duplicate_excess_rows": sum(count - 1 for count in raw.values()),
        "normalized_duplicate_groups": sum(len(indexes) > 1 for indexes in groups.values()),
        "normalized_duplicate_excess_rows": sum(len(indexes) - 1 for indexes in groups.values()),
        "contradictory_groups": len(conflicts) if labels_available else None,
        "contradictory_hashes": conflicts if labels_available else None,
        "projects": dict(sorted(Counter(str(row.get("project")) for row in rows).items())),
    }


def overlap_audit(splits):
    hashes = {name: set(_groups(rows)) for name, rows in splits.items()}
    result = {}
    for left, right in combinations(splits, 2):
        shared = hashes[left] & hashes[right]
        commits_left = {(r.get("project"), r.get("commit_id")) for r in splits[left] if r.get("commit_id")}
        commits_right = {(r.get("project"), r.get("commit_id")) for r in splits[right] if r.get("commit_id")}
        result[f"{left}__{right}"] = {
            "function_groups": len(shared),
            "left_rows": sum(fingerprint(r.get("func")) in shared for r in splits[left]),
            "right_rows": sum(fingerprint(r.get("func")) in shared for r in splits[right]),
            "shared_project_commits": len(commits_left & commits_right),
        }
    return result


def clean_development(train, validation, test_sources):
    """Preserve all test rows. Exclude every development match to a test hash.

    Quarantine conflicting training/validation label groups; do not majority vote.
    Deduplicate same-label development groups in official order. Validation takes
    precedence over training. Every removed row receives an auditable reason.
    No test labels are accepted here.
    """
    if any("target" in row for row in test_sources):
        raise ValueError("Test labels must remain sealed during development cleaning")
    test_hashes = set(_groups(test_sources))
    dev_labels = defaultdict(set)
    for row in [*train, *validation]:
        key = fingerprint(row.get("func"))
        if key and valid_label(row.get("target")):
            dev_labels[key].add(int(row["target"]))
    conflicts = {key for key, labels in dev_labels.items() if len(labels) > 1}
    retained = {"train": [], "validation": []}
    decisions = []
    validation_hashes = set()
    for split, rows in (("validation", validation), ("train", train)):
        seen = set()
        for index, row in enumerate(rows):
            key = fingerprint(row.get("func"))
            reasons = []
            if key is None:
                reasons.append("missing_or_invalid_function")
            if not valid_label(row.get("target")):
                reasons.append("missing_or_invalid_target")
            if key in test_hashes:
                reasons.append("matches_test_function")
            if key in conflicts:
                reasons.append("contradictory_development_labels")
            if split == "train" and key in validation_hashes:
                reasons.append("matches_validation_function")
            if key in seen:
                reasons.append("duplicate_within_split")
            if reasons:
                decisions.append({"split": split, "row_index": index, "id": row.get("id"), "hash": key, "reasons": reasons})
            else:
                retained[split].append(dict(row))
                seen.add(key)
        if split == "validation":
            validation_hashes = seen
    all_splits = {"train": train, "validation": validation, "test": test_sources}
    report = {
        "policy_version": POLICY_VERSION,
        "test_labels_used": False, "test_rows_modified": 0,
        "raw": {name: split_audit(rows, labels_available=name != "test") for name, rows in all_splits.items()},
        "overlap_before": overlap_audit(all_splits),
        "overlap_after": overlap_audit({**retained, "test": test_sources}),
        "cleaned": {name: split_audit(rows) for name, rows in retained.items()},
        "development_conflict_groups": len(conflicts),
        "removed_rows": len(decisions),
        "removal_reason_counts": dict(Counter(reason for decision in decisions for reason in decision["reasons"])),
    }
    if any(item["function_groups"] for item in report["overlap_after"].values()):
        raise ValueError("Function leakage remains after cleaning")
    return retained, report, decisions


def audit_test_after_selection(test, original_development):
    """Descriptive only. Never feed this post-selection report back to cleaning."""
    if any(not valid_label(row.get("target")) for row in test):
        raise ValueError("Official test has invalid labels; cannot evaluate the untouched holdout")
    labels = defaultdict(set)
    for row in original_development:
        key = fingerprint(row.get("func"))
        if key and valid_label(row.get("target")):
            labels[key].add(int(row["target"]))
    disagreement = sum(bool(labels.get(fingerprint(row.get("func")), set()) - {int(row["target"])}) for row in test)
    return {"test": split_audit(test), "test_rows_with_development_label_disagreement": disagreement,
            "test_rows_modified": 0, "used_for_model_selection": False}
