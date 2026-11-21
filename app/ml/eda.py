"""Reproducible development-set plots; never inspect test feature/label relations."""

from collections import Counter
from pathlib import Path

import numpy as np

from app.ml.features import FEATURE_NAMES
from app.ml.io import write_json


def describe(matrix):
    result = {}
    for index, name in enumerate(FEATURE_NAMES):
        values = matrix[:, index]
        observed = values[np.isfinite(values)]
        result[name] = {
            "missing": int(np.isnan(values).sum()), "observed": len(observed),
            "mean": float(observed.mean()) if len(observed) else None,
            "std": float(observed.std()) if len(observed) else None,
            "quantiles": dict(zip(["min", "p25", "median", "p75", "p95", "max"],
                                   np.quantile(observed, [0, .25, .5, .75, .95, 1]).tolist())) if len(observed) else None,
        }
    return result


def create_eda(matrices, labels, statuses, audit: dict, output: Path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    output.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.size": 9, "figure.dpi": 130, "axes.spines.top": False, "axes.spines.right": False})

    def save(fig, name):
        fig.tight_layout()
        fig.savefig(output / name, metadata={"Software": "Codebase Archaeologist"})
        plt.close(fig)

    summaries = {split: describe(matrix) for split, matrix in matrices.items()}
    class_summaries = {str(label): describe(matrices["train"][labels["train"] == label]) for label in (0, 1)}
    train = matrices["train"]
    correlation = np.full((len(FEATURE_NAMES), len(FEATURE_NAMES)), np.nan)
    for i in range(len(FEATURE_NAMES)):
        for j in range(len(FEATURE_NAMES)):
            mask = np.isfinite(train[:, i]) & np.isfinite(train[:, j])
            x, y = train[mask, i], train[mask, j]
            if len(x) > 1 and np.std(x) > 0 and np.std(y) > 0:
                correlation[i, j] = np.corrcoef(x, y)[0, 1]
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    splits = ["train", "validation", "test"]
    axes[0].bar(splits, [audit["raw"][s]["rows"] for s in splits], color="#3c8599")
    axes[0].set(title="Official split sizes", ylabel="Functions")
    for index, split in enumerate(("train", "validation")):
        counts = [int((labels[split] == label).sum()) for label in (0, 1)]
        axes[1].bar(np.arange(2) + index * .35, counts, width=.35, label=split)
    axes[1].set(xticks=[.175, 1.175], xticklabels=["Label 0", "Label 1"], title="Cleaned development labels (test sealed)", ylabel="Functions")
    axes[1].legend()
    save(fig, "split_and_label_counts.png")

    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    missing_names = list(audit["raw"]["train"]["missing"])
    axes[0].bar(missing_names, [audit["raw"]["train"]["missing"][name] for name in missing_names])
    axes[0].set(title="Missing fields in official training data", ylabel="Rows")
    axes[0].tick_params(axis="x", rotation=30)
    axes[1].bar(splits, [audit["raw"][s]["normalized_duplicate_excess_rows"] for s in splits])
    axes[1].set(title="Normalized duplicate excess rows", ylabel="Rows")
    save(fig, "missing_and_duplicates.png")

    fig, axes = plt.subplots(3, 4, figsize=(14, 10))
    for index, name in enumerate(FEATURE_NAMES):
        values = train[:, index]
        axes.flat[index].hist(np.log1p(values[np.isfinite(values)]), bins=30, color="#3c8599")
        axes.flat[index].set(title=name, xlabel="log(1 + value)", ylabel="Training functions")
    for ax in list(axes.flat)[len(FEATURE_NAMES):]:
        ax.set_visible(False)
    save(fig, "feature_distributions.png")

    fig, ax = plt.subplots(figsize=(10, 9))
    heatmap = ax.imshow(np.ma.masked_invalid(correlation), vmin=-1, vmax=1, cmap="coolwarm")
    ax.set(xticks=range(len(FEATURE_NAMES)), yticks=range(len(FEATURE_NAMES)),
           xticklabels=FEATURE_NAMES, yticklabels=FEATURE_NAMES,
           title="Training features: pairwise Pearson correlation")
    plt.setp(ax.get_xticklabels(), rotation=55, ha="right")
    fig.colorbar(heatmap, ax=ax)
    save(fig, "feature_correlations.png")

    fig, axes = plt.subplots(3, 4, figsize=(14, 10))
    for index, name in enumerate(FEATURE_NAMES):
        distributions = []
        for label in (0, 1):
            values = train[labels["train"] == label, index]
            distributions.append(np.log1p(values[np.isfinite(values)]))
        axes.flat[index].boxplot(distributions, tick_labels=["Label 0", "Label 1"], showfliers=False)
        axes.flat[index].set(title=name, ylabel="log(1 + value)")
    for ax in list(axes.flat)[len(FEATURE_NAMES):]:
        ax.set_visible(False)
    save(fig, "features_by_class.png")

    parse_counts = {split: dict(Counter(values)) for split, values in statuses.items()}
    observations = [
        f"Cleaning retained {len(train)} training and {len(matrices['validation'])} validation rows; removed {audit['removed_rows']} development rows.",
        f"Training label 1 fraction is {float(labels['train'].mean()):.4f}; this is a dataset prevalence, not repository risk.",
        f"Tree-sitter parsed {parse_counts['train'].get('ok', 0)} of {len(train)} training snippets without errors; structural failures are missing values, not zeros.",
        "Test labels and test feature distributions were not used for development EDA.",
        "Official splits share projects; identical-function removal does not establish project-, time- or commit-independent generalization.",
    ]
    pairs = [(abs(correlation[i, j]), FEATURE_NAMES[i], FEATURE_NAMES[j], correlation[i, j])
             for i in range(len(FEATURE_NAMES)) for j in range(i) if np.isfinite(correlation[i, j])]
    if pairs:
        _, left, right, value = max(pairs)
        observations.append(f"Strongest absolute training feature correlation: {left} / {right}, Pearson r={value:.4f}.")
    summary = {"scope": "cleaned training/validation only; raw test integrity counts without labels",
               "audit": audit, "feature_statistics": summaries, "training_features_by_class": class_summaries,
               "parse_status": parse_counts,
               "correlation": [[None if not np.isfinite(value) else float(value) for value in row] for row in correlation],
               "feature_order": list(FEATURE_NAMES), "observations": observations}
    write_json(output / "eda_summary.json", summary)
    (output / "observations.txt").write_text("\n".join(observations) + "\n", encoding="utf-8")
    return summary
