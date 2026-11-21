"""Three predeclared laptop-sized experiments, with training-only preprocessing."""

import math

from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

SEED = 42


def build_models():
    def pipeline(estimator, scale=False):
        steps = [("impute", SimpleImputer(strategy="median", keep_empty_features=True))]
        if scale:
            steps.append(("scale", StandardScaler()))
        steps.append(("classifier", estimator))
        return Pipeline(steps)

    return {
        "logistic_regression": pipeline(LogisticRegression(
            C=1.0, class_weight="balanced", solver="lbfgs", max_iter=2000, random_state=SEED), scale=True),
        "random_forest": pipeline(RandomForestClassifier(
            n_estimators=200, max_depth=12, min_samples_leaf=3, max_features="sqrt",
            class_weight="balanced", n_jobs=1, random_state=SEED)),
        "hist_gradient_boosting": pipeline(HistGradientBoostingClassifier(
            learning_rate=0.08, max_iter=160, max_leaf_nodes=15, min_samples_leaf=20,
            l2_regularization=1.0, class_weight="balanced", early_stopping=False, random_state=SEED)),
    }


def model_parameters(pipeline):
    # JSON has no NaN literal; record the imputer sentinel explicitly.
    return {name: {key: "NaN" if isinstance(value, float) and math.isnan(value) else value
                   for key, value in step.get_params(deep=False).items()}
            for name, step in pipeline.steps}
