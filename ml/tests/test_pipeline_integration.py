from copy import deepcopy

import pandas as pd
import pytest

from src.config import ALERT_CATEGORY_BY_RECOMMENDATION_CATEGORY, FEATURE_COLUMNS
from src.pipeline import run_project_pipeline
from src.what_if import simulate_scenario


def _record(index: int = 0) -> dict:
    data = pd.read_csv("ml/data/raw/land_acquisition_cases.csv")
    return data.loc[index, ["project_id", *FEATURE_COLUMNS]].to_dict()


def test_lower_risk_project_runs_through_full_pipeline() -> None:
    record = _record(0)
    record.update({"legal_disputes": 0, "ownership_conflicts": 0, "pending_court_cases": 0,
                   "pending_approvals": 0, "approval_delay_days": 0, "historical_delay_rate": 0,
                   "previous_stage_delay_days": 0, "documentation_completion_pct": 100,
                   "compensation_completion_pct": 100, "rehabilitation_completion_pct": 100})
    result = run_project_pipeline(record)
    assert result["project_id"] == record["project_id"]
    assert 0 <= result["prediction"]["risk_score"] <= 100
    assert result["prediction"]["risk_category"] == "Low"
    assert result["prediction"]["risk_score"] == result["explanation"]["risk_score"]
    assert isinstance(result["recommendations"]["recommendations"], list)
    assert isinstance(result["alerts"], list)


def test_high_risk_project_keeps_shap_recommendation_alert_traceability() -> None:
    record = _record(0)
    record.update({"legal_disputes": 20, "ownership_conflicts": 45, "pending_court_cases": 60,
                   "pending_approvals": 30, "approval_delay_days": 500, "historical_delay_rate": 1,
                   "previous_stage_delay_days": 600})
    result = run_project_pipeline(record)
    assert result["prediction"]["risk_category"] in {"High", "Critical"}
    positive_factors = [factor for factor in result["explanation"]["top_factors"] if factor["shap_value"] > 0]
    assert positive_factors
    recommendations = result["recommendations"]["recommendations"]
    assert recommendations
    for recommendation in recommendations:
        assert "SHAP +" in recommendation["reason"]
        assert any(factor["feature"] in recommendation["trigger"] for factor in positive_factors)
        assert any(alert["reason"] == recommendation["reason"] for alert in result["alerts"])
        expected = ALERT_CATEGORY_BY_RECOMMENDATION_CATEGORY[recommendation["category"]]
        assert any(alert["category"] == expected for alert in result["alerts"])


def test_what_if_uses_same_saved_prediction_contract_and_preserves_duration_limit() -> None:
    record = _record(0)
    before = deepcopy(record)
    result = simulate_scenario(record, {"pending_approvals": 0, "documentation_completion_pct": 95})
    assert record == before
    assert result["baseline"] == run_project_pipeline(record)["prediction"]
    assert result["impact"]["delay_days_change"] is None
    assert result["impact"]["delay_days_available"] is False


def test_pipeline_requires_project_identity_but_does_not_model_it() -> None:
    record = _record()
    record.pop("project_id")
    with pytest.raises(ValueError, match="project_id"):
        run_project_pipeline(record)
