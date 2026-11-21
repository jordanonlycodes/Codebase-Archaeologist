import json

import pytest

pytest.importorskip("sklearn")

from app.ml.evaluation import evaluate, select_model
from app.ml.estimators import build_models, model_parameters


def test_confusion_matrix_and_metrics_formula():
    # Arithmetic unit test, not a claimed dataset evaluation or training source.
    metrics = evaluate([0, 0, 1, 1], [.1, .9, .2, .8])
    assert metrics["confusion_matrix"] == [[1, 1], [1, 1]]
    assert metrics["accuracy"] == metrics["precision"] == metrics["recall"] == metrics["f1"] == .5
    assert metrics["roc_auc"] == .5


def test_single_class_auc_is_unavailable():
    assert evaluate([0, 0], [.1, .2])["roc_auc"] is None


@pytest.mark.parametrize("labels,probabilities", [([], []), ([1], [1.1]), ([2], [.5]), ([0, 1], [.5]), ([0], [float("nan")])])
def test_invalid_metric_inputs(labels, probabilities):
    with pytest.raises(ValueError):
        evaluate(labels, probabilities)


def test_selection_prefers_f1_then_recall_and_never_test():
    result = {
        "a": {"train": {"f1": .8}, "validation": {"f1": .7, "recall": .6, "false_positives": 1}},
        "b": {"train": {"f1": .9}, "validation": {"f1": .7, "recall": .8, "false_positives": 2}},
    }
    assert select_model(result) == "b"
    result["a"]["validation"]["f1"] = .71
    assert select_model(result) == "a"


def test_all_estimators_have_fixed_seed_and_training_preprocessors():
    models = build_models()
    assert set(models) == {"logistic_regression", "random_forest", "hist_gradient_boosting"}
    assert all(model["classifier"].random_state == 42 for model in models.values())
    assert all(model["impute"].strategy == "median" for model in models.values())
    assert "scale" in models["logistic_regression"].named_steps
    assert models["hist_gradient_boosting"]["classifier"].early_stopping is False
    assert {name: model_parameters(model) for name, model in models.items()} == {name: model_parameters(model) for name, model in build_models().items()}
    json.dumps({name: model_parameters(model) for name, model in models.items()}, allow_nan=False)
