"""Explicit offline inference adapter, intentionally not registered in FastAPI."""

from pathlib import Path

from app.analysis.models import AnalysisResult
from app.ml.features import feature_matrix
from app.ml.inference import RiskPrediction
from app.ml.model_store import load_pipeline


class LocalCFunctionModel:
    def __init__(self, directory: Path, *, trusted: bool = False):
        self.pipeline, self.metadata = load_pipeline(directory, trusted=trusted)

    def predict(self, analysis: AnalysisResult) -> RiskPrediction:
        raise NotImplementedError("Repository metrics do not contain C function source. Use predict_function; repository aggregation belongs to Task 3.")

    def predict_function(self, source: str) -> RiskPrediction:
        matrix, statuses = feature_matrix([source])
        if statuses != ["ok"]:
            raise ValueError(f"Prediction unavailable for this function: {statuses[0]}")
        probability = float(self.pipeline.predict_proba(matrix)[0, 1])
        return RiskPrediction(
            model_version=self.metadata["model_version"], risk_probability=probability,
            explanation="Estimated Devign label-1 probability from C syntax metrics. Uncalibrated research score; not a confirmed vulnerability or repository-wide risk score.",
        )
