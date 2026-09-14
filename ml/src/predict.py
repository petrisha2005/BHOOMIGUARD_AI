"""Artifact-backed inference for BhoomiGuard delay risk classification."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

import joblib
import pandas as pd

try:
    from .config import CLASSIFIER_MODEL_PATH, FEATURE_COLUMNS, RISK_THRESHOLDS
except ImportError:  # Allows direct execution/import from ml/src.
    from config import CLASSIFIER_MODEL_PATH, FEATURE_COLUMNS, RISK_THRESHOLDS


def risk_from_probability(delay_probability: float) -> tuple[float, str]:
    """Convert a delay probability to the normalized 0–100 decision-support score."""
    probability = min(max(float(delay_probability), 0.0), 1.0)
    score = round(probability * 100, 2)
    category = next(label for upper, label in RISK_THRESHOLDS if score < upper)
    return score, category


def predict_case(record: Mapping[str, Any], model_path: Path = CLASSIFIER_MODEL_PATH) -> dict[str, Any]:
    """Predict delay risk for one snapshot using the saved full preprocessing/model pipeline."""
    missing = set(FEATURE_COLUMNS).difference(record)
    if missing:
        raise ValueError(f"Record is missing required feature fields: {sorted(missing)}")
    model = joblib.load(model_path)
    features = pd.DataFrame([{column: record[column] for column in FEATURE_COLUMNS}])
    probability = float(model.predict_proba(features)[0, 1])
    risk_score, risk_category = risk_from_probability(probability)
    return {
        "delay_probability": round(probability, 4), "no_delay_probability": round(1 - probability, 4),
        "risk_score": risk_score, "risk_category": risk_category,
        "predicted_delay": bool(model.predict(features)[0]),
    }


class DelayDurationRegressor:
    """Interface placeholder; delay-duration regression is explicitly deferred to Step 2A."""

    def predict(self, _: Mapping[str, Any]) -> float:
        raise NotImplementedError("Delay-duration regression will be implemented in Step 2A.")
