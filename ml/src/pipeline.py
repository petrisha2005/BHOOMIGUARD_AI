"""Thin end-to-end orchestration of the existing BhoomiGuard intelligence stages."""

from __future__ import annotations

from typing import Any, Mapping

try:
    from .alerts import generate_alerts
    from .explain import explain_prediction
    from .predict import predict_case
    from .recommend import generate_recommendations
except ImportError:  # Allows direct execution/import from ml/src.
    from alerts import generate_alerts
    from explain import explain_prediction
    from predict import predict_case
    from recommend import generate_recommendations


def run_project_pipeline(project_input: Mapping[str, Any], top_k: int = 15) -> dict[str, Any]:
    """Run prediction, SHAP, recommendations, and alerts for one project snapshot.

    ``project_id`` identifies the alert stream but is intentionally not sent to the model;
    the saved prediction pipeline remains the single source of truth for risk output.
    """
    project_id = project_input.get("project_id")
    if not isinstance(project_id, str) or not project_id:
        raise ValueError("project_input must include a non-empty project_id for alert generation")
    prediction = predict_case(project_input)
    explanation = explain_prediction(project_input, top_k=top_k, prediction=prediction)
    recommendations = generate_recommendations(project_input, explanation=explanation, top_k=top_k)
    alerts = generate_alerts(project_id, recommendations)
    return {
        "project_id": project_id, "prediction": prediction, "explanation": explanation,
        "recommendations": recommendations, "alerts": alerts,
    }
