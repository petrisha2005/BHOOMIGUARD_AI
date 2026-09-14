import pytest

from src.alerts import generate_alerts


def _recommendation(category: str = "Compensation", priority: str = "HIGH", escalation: bool = True) -> dict:
    return {
        "category": category, "priority": priority, "action": f"Address {category.lower()} blocker.",
        "reason": "Model factors increasing predicted risk: Pending compensation cases (SHAP +0.420).",
        "trigger": "Pending compensation cases (SHAP +0.420)", "responsible_role": "Compensation/Finance Officer",
        "suggested_deadline_days": 5, "escalation_required": escalation,
        "monitoring": "Track the affected cases until closure.",
    }


def _output(risk_category: str = "High", recommendations: list[dict] | None = None) -> dict:
    return {"overall_risk": {"delay_probability": .81, "risk_score": 81, "risk_category": risk_category,
                               "predicted_delay": True}, "recommendations": recommendations or []}


@pytest.mark.parametrize(("priority", "risk_category", "expected"), [
    ("HIGH", "High", "HIGH"), ("CRITICAL", "Critical", "CRITICAL"),
    ("MEDIUM", "Moderate", "MEDIUM"), ("LOW", "Low", "LOW"),
])
def test_alert_severity_follows_controlled_priority_mapping(priority: str, risk_category: str, expected: str) -> None:
    alert = generate_alerts("BG-100", _output(risk_category, [_recommendation(priority=priority)]))[0]
    assert alert["severity"] == expected


def test_escalation_role_deadline_and_shap_traceability_are_preserved() -> None:
    recommendation = _recommendation()
    alert = generate_alerts("BG-100", _output(recommendations=[recommendation]))[0]
    assert alert["escalation_required"] is True
    assert alert["responsible_role"] == recommendation["responsible_role"]
    assert alert["deadline_days"] == recommendation["suggested_deadline_days"]
    assert alert["reason"] == recommendation["reason"]
    assert alert["trigger"] == recommendation["trigger"]
    assert "SHAP +0.420" in alert["reason"]


@pytest.mark.parametrize(("recommendation_category", "alert_category"), [
    ("Compensation", "COMPENSATION"), ("Legal / Ownership", "LEGAL_OWNERSHIP"),
    ("Documentation", "DOCUMENTATION"), ("Approvals", "APPROVAL"),
    ("Rehabilitation & Resettlement", "REHABILITATION_RESETTLEMENT"),
    ("Inter-department Coordination", "COORDINATION"),
])
def test_alert_category_mapping_and_open_initial_status(recommendation_category: str, alert_category: str) -> None:
    alert = generate_alerts("BG-100", _output(recommendations=[_recommendation(recommendation_category)]))[0]
    assert alert["category"] == alert_category
    assert alert["status"] == "OPEN"


def test_alert_id_and_output_are_deterministic() -> None:
    payload = _output(recommendations=[_recommendation()])
    assert generate_alerts("BG-100", payload) == generate_alerts("BG-100", payload)


def test_duplicate_recommendation_category_creates_one_alert() -> None:
    result = generate_alerts("BG-100", _output(recommendations=[_recommendation(), _recommendation()]))
    assert len(result) == 1


def test_distinct_recommendations_create_distinct_alerts() -> None:
    result = generate_alerts("BG-100", _output(recommendations=[
        _recommendation("Compensation"), _recommendation("Documentation", "MEDIUM", False),
    ]))
    assert len(result) == 2
    assert {alert["category"] for alert in result} == {"COMPENSATION", "DOCUMENTATION"}


def test_no_recommendations_produces_no_inappropriate_alerts() -> None:
    assert generate_alerts("BG-100", _output("Low")) == []


def test_alert_contract_contains_required_fields() -> None:
    alert = generate_alerts("BG-100", _output(recommendations=[_recommendation()]))[0]
    required = {"alert_id", "project_id", "severity", "category", "title", "message", "project_risk",
                "reason", "trigger", "recommended_action", "responsible_role", "deadline_days",
                "escalation_required", "status", "monitoring"}
    assert required.issubset(alert)
