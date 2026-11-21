"""Integration seam for a future independently validated model.

No model is loaded, no training occurs, and current HTTP analysis does not invoke
inference. A future provider consumes the versioned deterministic result.
"""

from dataclasses import dataclass
from typing import Protocol

from app.analysis.models import AnalysisResult


@dataclass(frozen=True)
class RiskPrediction:
    model_version: str
    risk_probability: float
    explanation: str


class RiskModel(Protocol):
    def predict(self, analysis: AnalysisResult) -> RiskPrediction:
        """Return a calibrated prediction from a trained, validated model."""
        ...


class UnavailableModel:
    def predict(self, analysis: AnalysisResult) -> RiskPrediction:
        raise NotImplementedError("No trained risk model is configured.")
