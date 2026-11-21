"""Inference contracts. HTTP analysis does not invoke or load a model.

Task 1's repository contract remains available. Function models use source text
through a separate compatible contract and return the same RiskPrediction type.
Repository totals cannot substitute for function-level features.
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


class FunctionRiskModel(Protocol):
    def predict_function(self, source: str) -> RiskPrediction:
        """Score one parseable C function; no repository aggregation is implied."""
        ...
