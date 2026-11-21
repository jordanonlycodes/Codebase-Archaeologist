"""Fixed-threshold metrics and validation-only model selection."""

import numpy as np
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score

THRESHOLD = 0.5


def evaluate(y, probabilities):
    y = np.asarray(y)
    probabilities = np.asarray(probabilities, dtype=float)
    if y.ndim != 1 or probabilities.shape != y.shape or not len(y):
        raise ValueError("Nonempty labels and one probability per row are required")
    if not np.isin(y, [0, 1]).all() or not np.isfinite(probabilities).all() or ((probabilities < 0) | (probabilities > 1)).any():
        raise ValueError("Invalid binary labels or probabilities")
    predicted = (probabilities >= THRESHOLD).astype(int)
    matrix = confusion_matrix(y, predicted, labels=[0, 1])
    tn, fp, fn, tp = matrix.ravel()
    return {
        "rows": len(y), "threshold": THRESHOLD,
        "class_counts": {str(label): int((y == label).sum()) for label in (0, 1)},
        "accuracy": float(accuracy_score(y, predicted)),
        "precision": float(precision_score(y, predicted, zero_division=0)),
        "recall": float(recall_score(y, predicted, zero_division=0)),
        "f1": float(f1_score(y, predicted, zero_division=0)),
        "roc_auc": float(roc_auc_score(y, probabilities)) if len(np.unique(y)) == 2 else None,
        "confusion_matrix": matrix.tolist(), "confusion_matrix_order": [["TN", "FP"], ["FN", "TP"]],
        "false_positive_rate": float(fp / (fp + tn)) if fp + tn else None,
        "false_negatives": int(fn), "false_positives": int(fp),
    }


def select_model(comparison):
    """Max F1, then recall, then fewer false positives, then smaller F1 gap.

    Parameters and threshold are fixed in advance. Alphabetical name is the
    final deterministic tie-breaker; no test results are accepted here.
    """
    if not comparison:
        raise ValueError("No validation results are available")
    return sorted(comparison, key=lambda name: (
        -comparison[name]["validation"]["f1"],
        -comparison[name]["validation"]["recall"],
        comparison[name]["validation"]["false_positives"],
        abs(comparison[name]["train"]["f1"] - comparison[name]["validation"]["f1"]), name,
    ))[0]
