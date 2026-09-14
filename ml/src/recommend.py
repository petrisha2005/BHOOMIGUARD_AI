"""Deterministic action recommendations grounded in saved-model SHAP contributions."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Mapping

try:
    from .config import (CRITICAL_CONTRIBUTION_THRESHOLD, PRIORITY_DEADLINE_DAYS,
                         RECOMMENDATION_FEATURE_CATEGORIES, RECOMMENDATION_TEMPLATES, RISK_CATEGORY_PRIORITY)
    from .explain import explain_prediction
except ImportError:  # Allows direct execution/import from ml/src.
    from config import (CRITICAL_CONTRIBUTION_THRESHOLD, PRIORITY_DEADLINE_DAYS,
                        RECOMMENDATION_FEATURE_CATEGORIES, RECOMMENDATION_TEMPLATES, RISK_CATEGORY_PRIORITY)
    from explain import explain_prediction


def _raw_feature_name(transformed_feature: str) -> str | None:
    """Extract an original numerical feature from a transformed model feature name."""
    if transformed_feature.startswith("numeric__"):
        return transformed_feature.removeprefix("numeric__")
    return None


def _priority(risk_category: str, strongest_contribution: float) -> str:
    """Derive a bounded urgency level; Critical requires both critical risk and strong evidence."""
    if risk_category not in RISK_CATEGORY_PRIORITY:
        raise ValueError(f"Unknown risk category: {risk_category}")
    if risk_category == "Critical" and strongest_contribution >= CRITICAL_CONTRIBUTION_THRESHOLD:
        return "CRITICAL"
    return RISK_CATEGORY_PRIORITY[risk_category]


def _factor_description(factor: Mapping[str, Any]) -> str:
    """Preserve the SHAP-derived evidence in officer-readable wording."""
    return f"{factor['feature']} (SHAP +{float(factor['shap_value']):.3f})"


def generate_recommendations(
    record: Mapping[str, Any], explanation: Mapping[str, Any] | None = None, top_k: int = 15,
) -> dict[str, Any]:
    """Convert positive SHAP risk contributors into de-duplicated operational interventions.

    The optional ``explanation`` makes the rules layer independently testable. If omitted,
    it requests an explanation from the saved ML pipeline. It never infers factors itself.
    """
    explanation = explanation or explain_prediction(record, top_k=top_k)
    risk_category = str(explanation["risk_category"])
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for factor in explanation.get("top_factors", []):
        shap_value = float(factor.get("shap_value", 0))
        feature_name = _raw_feature_name(str(factor.get("transformed_feature", "")))
        category = RECOMMENDATION_FEATURE_CATEGORIES.get(feature_name)
        if shap_value > 0 and category:
            grouped[category].append(factor)

    recommendations: list[dict[str, Any]] = []
    for category, factors in grouped.items():
        strongest = max(abs(float(factor["shap_value"])) for factor in factors)
        priority = _priority(risk_category, strongest)
        template = RECOMMENDATION_TEMPLATES[category]
        trigger = "; ".join(_factor_description(factor) for factor in factors)
        recommendations.append({
            "category": category, "priority": priority, "action": template["action"],
            "reason": f"Model factors increasing predicted risk: {trigger}.", "trigger": trigger,
            "responsible_role": template["responsible_role"],
            "suggested_deadline_days": PRIORITY_DEADLINE_DAYS[priority],
            "escalation_required": priority in {"CRITICAL", "HIGH"}, "monitoring": template["monitoring"],
        })
    priority_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    recommendations.sort(key=lambda item: (priority_order[item["priority"]], item["category"]))
    return {
        "overall_risk": {key: explanation[key] for key in ("delay_probability", "risk_score", "risk_category", "predicted_delay")},
        "recommendations": recommendations,
        "monitoring_note": "Recalculate risk after material intervention updates; recommendations are model-guided, not causal findings.",
    }
