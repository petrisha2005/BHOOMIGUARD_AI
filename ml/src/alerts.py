"""Deterministic, service-independent early-warning alert generation."""

from __future__ import annotations

from hashlib import sha256
from typing import Any, Mapping

try:
    from .config import (ALERT_CATEGORY_BY_RECOMMENDATION_CATEGORY, ALERT_CRITICAL_RISK_CATEGORY,
                         ALERT_ELIGIBLE_PRIORITIES, ALERT_ESCALATE_HIGH_WITH_RECOMMENDATION_FLAG, ALERT_ESCALATION_SEVERITIES,
                         ALERT_INITIAL_STATUS, ALERT_SEVERITY_BY_RECOMMENDATION_PRIORITY)
except ImportError:  # Allows direct execution/import from ml/src.
    from config import (ALERT_CATEGORY_BY_RECOMMENDATION_CATEGORY, ALERT_CRITICAL_RISK_CATEGORY,
                        ALERT_ELIGIBLE_PRIORITIES, ALERT_ESCALATE_HIGH_WITH_RECOMMENDATION_FLAG, ALERT_ESCALATION_SEVERITIES,
                        ALERT_INITIAL_STATUS, ALERT_SEVERITY_BY_RECOMMENDATION_PRIORITY)


def _alert_id(project_id: str, category: str, action: str) -> str:
    """Create a stable ID for one actionable category in one project without persistence."""
    digest = sha256(f"{project_id}|{category}|{action}".encode("utf-8")).hexdigest()[:16]
    return f"BG-ALERT-{digest.upper()}"


def _severity(recommendation: Mapping[str, Any], overall_risk: Mapping[str, Any]) -> str:
    """Map priority to alert severity, upgrading urgent actions in a critical-risk project."""
    priority = str(recommendation["priority"])
    if priority not in ALERT_SEVERITY_BY_RECOMMENDATION_PRIORITY:
        raise ValueError(f"Unknown recommendation priority: {priority}")
    if priority == "HIGH" and overall_risk.get("risk_category") == ALERT_CRITICAL_RISK_CATEGORY:
        return "CRITICAL"
    return ALERT_SEVERITY_BY_RECOMMENDATION_PRIORITY[priority]


def _requires_escalation(severity: str, recommendation: Mapping[str, Any]) -> bool:
    """Apply the controlled escalation policy without external notification side effects."""
    if severity in ALERT_ESCALATION_SEVERITIES:
        return True
    return bool(
        severity == "HIGH" and ALERT_ESCALATE_HIGH_WITH_RECOMMENDATION_FLAG
        and recommendation.get("escalation_required", False)
    )


def generate_alerts(project_id: str, recommendation_output: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Convert Stage 4 recommendations into one OPEN alert per distinct action category.

    This function only creates structured alert records. Persistence, acknowledgement,
    notifications, and risk recalculation are deliberately deferred to future stages.
    """
    if not project_id:
        raise ValueError("project_id is required for stable alert generation")
    overall_risk = recommendation_output["overall_risk"]
    unique_recommendations: dict[str, Mapping[str, Any]] = {}
    for recommendation in recommendation_output.get("recommendations", []):
        if recommendation.get("priority") not in ALERT_ELIGIBLE_PRIORITIES:
            continue
        category = str(recommendation["category"])
        unique_recommendations.setdefault(category, recommendation)

    alerts: list[dict[str, Any]] = []
    for category, recommendation in unique_recommendations.items():
        alert_category = ALERT_CATEGORY_BY_RECOMMENDATION_CATEGORY.get(category)
        if alert_category is None:
            raise ValueError(f"No alert category configured for recommendation category: {category}")
        severity = _severity(recommendation, overall_risk)
        title = f"{category} action required"
        message = (
            f"{category} needs attention because model findings indicate it is contributing to the predicted delay risk. "
            f"Recommended next step: {recommendation['action']}"
        )
        alerts.append({
            "alert_id": _alert_id(project_id, category, str(recommendation["action"])), "project_id": project_id,
            "severity": severity, "category": alert_category, "title": title, "message": message,
            "project_risk": overall_risk["risk_score"], "risk_category": overall_risk["risk_category"],
            "reason": recommendation["reason"], "trigger": recommendation["trigger"],
            "recommended_action": recommendation["action"], "responsible_role": recommendation["responsible_role"],
            "deadline_days": recommendation["suggested_deadline_days"],
            "escalation_required": _requires_escalation(severity, recommendation),
            "status": ALERT_INITIAL_STATUS, "monitoring": recommendation["monitoring"],
        })
    severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}
    return sorted(alerts, key=lambda alert: (severity_order[alert["severity"]], alert["category"]))
