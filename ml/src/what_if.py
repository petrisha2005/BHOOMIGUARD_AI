"""Deterministic scenario simulation using the saved BhoomiGuard prediction pipeline."""

from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
from numbers import Real
from typing import Any, Mapping

import pandas as pd

try:
    from .config import (CATEGORICAL_COLUMNS, FEATURE_COLUMNS, PROJECT_TYPES, RAW_DATA_PATH, SCENARIO_INTEGER_FEATURES,
                         SCENARIO_MEANINGFUL_RISK_CHANGE_POINTS, SCENARIO_MINIMUMS, SCENARIO_PERCENTAGE_FEATURES,
                         SCENARIO_UNIT_INTERVAL_FEATURES, STAGE_NAMES, STATE_DISTRICTS)
    from .predict import predict_case
except ImportError:  # Allows direct execution/import from ml/src.
    from config import (CATEGORICAL_COLUMNS, FEATURE_COLUMNS, PROJECT_TYPES, RAW_DATA_PATH, SCENARIO_INTEGER_FEATURES,
                        SCENARIO_MEANINGFUL_RISK_CHANGE_POINTS, SCENARIO_MINIMUMS, SCENARIO_PERCENTAGE_FEATURES,
                        SCENARIO_UNIT_INTERVAL_FEATURES, STAGE_NAMES, STATE_DISTRICTS)
    from predict import predict_case


@lru_cache(maxsize=1)
def _training_support() -> dict[str, tuple[float, float, float, float]]:
    """Derive numeric normal and observed support from the saved model's prototype dataset."""
    data = pd.read_csv(RAW_DATA_PATH)
    return {
        feature: (float(data[feature].min()), float(data[feature].quantile(.01)),
                  float(data[feature].quantile(.99)), float(data[feature].max()))
        for feature in SCENARIO_INTEGER_FEATURES + SCENARIO_PERCENTAGE_FEATURES + SCENARIO_UNIT_INTERVAL_FEATURES + ("land_area_acres",)
    }


def _validate_value(feature: str, value: Any) -> str | None:
    """Validate one changed input against the original model-input schema constraints."""
    if feature in CATEGORICAL_COLUMNS:
        allowed = {"project_type": PROJECT_TYPES, "state": tuple(STATE_DISTRICTS),
                   "current_stage": STAGE_NAMES}.get(feature)
        if feature == "district":
            if not isinstance(value, str):
                raise ValueError("district must be a string")
            if value not in {district for districts in STATE_DISTRICTS.values() for district in districts}:
                raise ValueError(f"Invalid district: {value}")
        elif value not in allowed:
            raise ValueError(f"Invalid {feature}: {value}")
        return None
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{feature} must be numeric")
    if feature in SCENARIO_INTEGER_FEATURES and int(value) != value:
        raise ValueError(f"{feature} must be an integer")
    minimum = SCENARIO_MINIMUMS.get(feature, 0)
    maximum = 100 if feature in SCENARIO_PERCENTAGE_FEATURES else 1 if feature in SCENARIO_UNIT_INTERVAL_FEATURES else None
    if value < minimum or (maximum is not None and value > maximum):
        upper = f" and at most {maximum}" if maximum is not None else ""
        raise ValueError(f"{feature} must be at least {minimum}{upper}")
    observed_minimum, normal_minimum, normal_maximum, observed_maximum = _training_support()[feature]
    if value < observed_minimum or value > observed_maximum:
        raise ValueError(
            f"{feature}={value} is outside observed training support [{observed_minimum}, {observed_maximum}]"
        )
    if value < normal_minimum or value > normal_maximum:
        return "edge_of_training_support"
    return "within_normal_training_support"


def validate_scenario_changes(original: Mapping[str, Any], changes: Mapping[str, Any]) -> dict[str, str]:
    """Reject unknown, invalid, and incompatible scenario changes before prediction."""
    if not changes:
        raise ValueError("At least one scenario change is required")
    support: dict[str, str] = {}
    for feature, value in changes.items():
        if feature not in FEATURE_COLUMNS:
            raise ValueError(f"Unknown scenario feature: {feature}")
        status = _validate_value(feature, value)
        if status is not None:
            support[feature] = status
    final_state = changes.get("state", original.get("state"))
    final_district = changes.get("district", original.get("district"))
    if final_district not in STATE_DISTRICTS.get(final_state, ()):
        raise ValueError(f"district '{final_district}' is not valid for state '{final_state}'")
    return support


def _transition(baseline_category: str, scenario_category: str, change: float) -> str:
    """Describe category/risk direction from the existing shared risk system."""
    if baseline_category != scenario_category:
        return f"{baseline_category} → {scenario_category}"
    if change >= SCENARIO_MEANINGFUL_RISK_CHANGE_POINTS:
        return "Risk increased"
    if change <= -SCENARIO_MEANINGFUL_RISK_CHANGE_POINTS:
        return "Risk reduced"
    return "No meaningful improvement"


def _interpret(baseline: Mapping[str, Any], scenario: Mapping[str, Any], change: float) -> str:
    """Generate a factual projection statement from actual pipeline outputs."""
    if change >= SCENARIO_MEANINGFUL_RISK_CHANGE_POINTS:
        return (f"The selected scenario increases predicted delay risk from {baseline['risk_score']:.2f}% "
                f"to {scenario['risk_score']:.2f}% and should be reviewed.")
    if change <= -SCENARIO_MEANINGFUL_RISK_CHANGE_POINTS:
        return (f"The selected changes reduce predicted delay risk from {baseline['risk_score']:.2f}% "
                f"to {scenario['risk_score']:.2f}% ({change:.2f} percentage points).")
    return "The selected changes produce minimal change in predicted delay risk."


def simulate_scenario(original: Mapping[str, Any], changes: Mapping[str, Any]) -> dict[str, Any]:
    """Compare original inputs with a validated multi-factor scenario via ``predict_case``.

    No delay-duration model exists yet, so duration impact is explicitly unavailable rather
    than estimated with a rule. Original input data is copied and never mutated.
    """
    support = validate_scenario_changes(original, changes)
    scenario_input = deepcopy(dict(original))
    scenario_input.update(changes)
    baseline = predict_case(original)
    scenario = predict_case(scenario_input)
    risk_change = round(float(scenario["risk_score"] - baseline["risk_score"]), 2)
    changed = {feature: {"before": original[feature], "after": scenario_input[feature]} for feature in changes}
    return {
        "baseline": baseline, "scenario": scenario,
        "impact": {
            "risk_score_change_percentage_points": risk_change,
            "risk_reduced": risk_change <= -SCENARIO_MEANINGFUL_RISK_CHANGE_POINTS,
            "risk_increased": risk_change >= SCENARIO_MEANINGFUL_RISK_CHANGE_POINTS,
            "risk_category_transition": _transition(baseline["risk_category"], scenario["risk_category"], risk_change),
            "delay_days_change": None, "delay_days_available": False,
        },
        "changes": changed, "baseline_input": deepcopy(dict(original)), "scenario_input": scenario_input,
        "training_support": {
            "status": "edge_of_training_support" if "edge_of_training_support" in support.values() else "within_normal_training_support",
            "feature_statuses": support,
            "note": "Scenario support is derived from the synthetic training dataset; edge values are model projections with added uncertainty.",
        },
        "interpretation": _interpret(baseline, scenario, risk_change),
        "duration_note": "Delay-duration comparison is unavailable until the planned duration-regression model is implemented.",
    }
