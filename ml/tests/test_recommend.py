import pandas as pd
import pytest

from src.config import FEATURE_COLUMNS, PRIORITY_DEADLINE_DAYS
from src.recommend import generate_recommendations


def _record() -> dict:
    data = pd.read_csv("ml/data/raw/land_acquisition_cases.csv")
    return data.loc[0, list(FEATURE_COLUMNS)].to_dict()


def _explanation(risk_category: str, factors: list[dict]) -> dict:
    return {
        "delay_probability": .81, "risk_score": 81, "risk_category": risk_category,
        "predicted_delay": True, "top_factors": factors,
    }


def _factor(feature: str, shap_value: float = .42) -> dict:
    return {"feature": feature.replace("_", " ").title(), "value": 1,
            "shap_value": shap_value, "direction": "increases_risk",
            "transformed_feature": f"numeric__{feature}"}


@pytest.mark.parametrize(("feature", "category"), [
    ("compensation_pending_cases", "Compensation"),
    ("ownership_conflicts", "Legal / Ownership"),
    ("missing_documents", "Documentation"),
    ("pending_approvals", "Approvals"),
    ("rehabilitation_completion_pct", "Rehabilitation & Resettlement"),
    ("stakeholder_response_delay_days", "Inter-department Coordination"),
])
def test_shap_driven_risk_factor_maps_to_its_operational_category(feature: str, category: str) -> None:
    result = generate_recommendations(_record(), _explanation("High", [_factor(feature)]))
    recommendation = result["recommendations"][0]
    assert recommendation["category"] == category
    assert "SHAP +0.420" in recommendation["reason"]
    assert recommendation["priority"] == "HIGH"


def test_multiple_drivers_are_deduplicated_and_all_preserved() -> None:
    factors = [_factor("compensation_pending_cases"), _factor("average_compensation_delay_days", .22),
               _factor("legal_disputes", .45)]
    result = generate_recommendations(_record(), _explanation("Critical", factors))
    recommendations = result["recommendations"]
    assert [item["category"] for item in recommendations] == ["Compensation", "Legal / Ownership"]
    assert "Average Compensation Delay Days" in recommendations[0]["reason"]
    assert recommendations[0]["priority"] == "CRITICAL"


def test_low_risk_or_reducing_factors_do_not_create_actions() -> None:
    result = generate_recommendations(_record(), _explanation("Low", [_factor("missing_documents", -.3)]))
    assert result["recommendations"] == []


def test_recommendation_contract_priorities_and_deadlines_are_valid() -> None:
    result = generate_recommendations(_record(), _explanation("Moderate", [_factor("pending_approvals")]))
    recommendation = result["recommendations"][0]
    required = {"category", "priority", "action", "reason", "trigger", "responsible_role",
                "suggested_deadline_days", "escalation_required", "monitoring"}
    assert required.issubset(recommendation)
    assert recommendation["priority"] in PRIORITY_DEADLINE_DAYS
    assert recommendation["suggested_deadline_days"] == PRIORITY_DEADLINE_DAYS[recommendation["priority"]]


def test_same_shap_input_produces_deterministic_recommendations() -> None:
    explanation = _explanation("High", [_factor("pending_approvals"), _factor("missing_documents")])
    assert generate_recommendations(_record(), explanation) == generate_recommendations(_record(), explanation)
