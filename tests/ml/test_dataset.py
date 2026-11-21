from copy import deepcopy

import pytest

from app.ml.dataset import clean_development, fingerprint, split_audit, audit_test_after_selection


def row(source, label=0, identifier=0):
    # These records exercise cleaning logic only. They are never model-training data.
    return {"func": source, "target": label, "id": identifier, "project": "fixture", "commit_id": "fixture"}


def sealed(source):
    return {key: value for key, value in row(source).items() if key != "target"}


def test_leakage_precedence_and_test_immutability():
    train = [row("train"), row("shared validation"), row("test duplicate")]
    validation = [row("shared validation"), row("test duplicate")]
    test = [sealed("test duplicate"), sealed("test duplicate")]
    original = deepcopy(test)
    cleaned, report, removed = clean_development(train, validation, test)
    assert [r["func"] for r in cleaned["train"]] == ["train"]
    assert [r["func"] for r in cleaned["validation"]] == ["shared validation"]
    assert test == original
    assert report["test_rows_modified"] == 0
    assert report["raw"]["test"]["labels"] is None
    assert all(item["function_groups"] == 0 for item in report["overlap_after"].values())
    assert len(removed) == 3


def test_contradictions_quarantined_without_majority_vote():
    train = [row("conflict", 0), row("conflict", 0), row("safe", 0)]
    validation = [row("conflict", 1), row("another", 1)]
    cleaned, audit, removed = clean_development(train, validation, [])
    assert audit["development_conflict_groups"] == 1
    assert all(r["func"] != "conflict" for rows in cleaned.values() for r in rows)
    assert len(removed) == 3
    assert all("contradictory_development_labels" in r["reasons"] for r in removed)


def test_same_label_duplicates_and_missing_values_reported():
    train = [row("same", 1, 1), row(" same\r\n", 1, 2), row(None), row("bad label", None)]
    cleaned, report, decisions = clean_development(train, [], [])
    assert [r["id"] for r in cleaned["train"]] == [1]
    assert report["raw"]["train"]["missing"]["func"] == 1
    assert report["raw"]["train"]["invalid_labels"] == 1
    assert report["removed_rows"] == 3
    assert len(decisions) == 3


def test_test_labels_rejected_during_preparation():
    with pytest.raises(ValueError, match="sealed"):
        clean_development([], [], [row("test", 1)])


def test_test_conflicts_only_reported_after_selection():
    test = [row("same", 0), row("same", 1)]
    before = deepcopy(test)
    report = audit_test_after_selection(test, [row("same", 0)])
    assert report["test"]["contradictory_groups"] == 1
    assert report["test_rows_with_development_label_disagreement"] == 1
    assert test == before


def test_cleaning_is_reproducible_and_labels_do_not_change_hashes():
    train, validation, test = [row("a"), row("a")], [row("b", 1)], [sealed("c")]
    assert clean_development(train, validation, test) == clean_development(train, validation, test)
    assert fingerprint("a\r\nb") == fingerprint("a\nb")
    assert fingerprint("a b") != fingerprint("ab")
    assert fingerprint(42) is None


def test_invalid_test_label_stops_instead_of_dropping_holdout():
    with pytest.raises(ValueError, match="invalid labels"):
        audit_test_after_selection([row("a", None)], [])


def test_invalid_labels_are_not_coerced_from_strings_or_floats():
    audit = split_audit([row("a", "1"), row("b", 1.0), row("c", True)])
    assert audit["invalid_labels"] == 2
    assert audit["labels"] == {"1": 1}
