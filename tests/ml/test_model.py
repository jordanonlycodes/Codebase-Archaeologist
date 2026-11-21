from pathlib import Path

import pytest

np = pytest.importorskip("numpy")
pytest.importorskip("sklearn")
pytest.importorskip("tree_sitter")
pytest.importorskip("pyarrow")

from threadpoolctl import threadpool_limits
from app.ml.acquire import DEFAULT_RAW
from app.ml.c_model import LocalCFunctionModel
from app.ml.dataset import load_split
from app.ml.estimators import build_models
from app.ml.features import extract_features, feature_matrix, FEATURE_NAMES
from app.ml.io import read_json, write_json
from app.ml.model_store import load_pipeline, save_pipeline
from app.ml.train import test_once as evaluate_holdout_once


@pytest.fixture(scope="module")
def real_training_sample():
    if not (DEFAULT_RAW / "manifest.json").exists():
        pytest.skip("Model fitting tests require the legitimate downloaded dataset; no labels are fabricated")
    selected = []
    for row in load_split(DEFAULT_RAW, "train"):
        if extract_features(row["func"]).parse_status == "ok":
            selected.append(row)
        if len(selected) == 128:
            break
    assert {row["target"] for row in selected} == {False, True}
    matrix, _ = feature_matrix(row["func"] for row in selected)
    labels = np.array([int(row["target"]) for row in selected])
    return selected, matrix, labels


@pytest.fixture(scope="module")
def fitted(real_training_sample):
    _, matrix, labels = real_training_sample
    pipeline = build_models()["logistic_regression"]
    with threadpool_limits(limits=1):
        pipeline.fit(matrix, labels)
    return pipeline


def test_model_round_trip_and_shared_feature_compatibility(tmp_path, fitted, real_training_sample):
    rows, matrix, _ = real_training_sample
    save_pipeline(fitted, tmp_path, {"model_version": "test-real-training-subset"})
    loaded, _ = load_pipeline(tmp_path, trusted=True)
    np.testing.assert_array_equal(fitted.predict_proba(matrix), loaded.predict_proba(matrix))
    model = LocalCFunctionModel(tmp_path, trusted=True)
    prediction = model.predict_function(rows[0]["func"])
    assert prediction.risk_probability == loaded.predict_proba(matrix[:1])[0, 1]
    assert prediction.model_version == "test-real-training-subset"
    assert "Uncalibrated" in prediction.explanation
    with pytest.raises(NotImplementedError, match="Repository metrics"):
        model.predict(None)
    with pytest.raises(ValueError, match="unavailable"):
        model.predict_function("int bad( {")


def test_training_reproducibility_on_small_authentic_subset(fitted, real_training_sample):
    # Two bounded unit-test fits on 128 genuine training rows, never full experiments.
    _, matrix, labels = real_training_sample
    second = build_models()["logistic_regression"]
    with threadpool_limits(limits=1):
        second.fit(matrix, labels)
    np.testing.assert_array_equal(fitted.predict_proba(matrix), second.predict_proba(matrix))


def test_untrusted_load_rejected(tmp_path):
    with pytest.raises(ValueError, match="trusted"):
        load_pipeline(tmp_path)


@pytest.mark.parametrize("change", ["schema", "checksum", "environment"])
def test_incompatible_artifacts_rejected(tmp_path, fitted, change):
    save_pipeline(fitted, tmp_path, {"model_version": "fixture"})
    metadata = read_json(tmp_path / "metadata.json")
    if change == "schema":
        metadata["feature_names"] = list(reversed(FEATURE_NAMES))
    elif change == "checksum":
        metadata["pipeline_sha256"] = "0" * 64
    else:
        metadata["environment"]["scikit-learn"] = "0.0"
    write_json(tmp_path / "metadata.json", metadata)
    with pytest.raises(ValueError):
        load_pipeline(tmp_path, trusted=True)


def test_interrupted_test_evaluation_cannot_run_again(tmp_path, monkeypatch):
    (tmp_path / "test_evaluation_started.json").write_text("{}")
    monkeypatch.setattr("app.ml.train.load_split", lambda *args, **kwargs: pytest.fail("Holdout must not be read"))
    with pytest.raises(FileExistsError):
        evaluate_holdout_once(tmp_path, None, Path("unused"), {"model": "fixture"})


def test_existing_evaluation_reused_without_reading_test(tmp_path, monkeypatch):
    write_json(tmp_path / "test_evaluation.json", {"status": "already_evaluated"})
    monkeypatch.setattr("app.ml.train.load_split", lambda *args, **kwargs: pytest.fail("Holdout must not be read"))
    assert evaluate_holdout_once(tmp_path, None, Path("unused"), {}) == {"status": "already_evaluated"}
