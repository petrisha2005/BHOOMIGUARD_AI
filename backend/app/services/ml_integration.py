"""Local adapter between the FastAPI application and BhoomiGuard's ML package.

This module deliberately owns no prediction, explanation, recommendation, alert, or
scenario policy.  It only adapts validated application records to the canonical ML
contract and persists the ML package's structured result in the existing tables.
"""

from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path
from typing import Any, Mapping

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Alert, Prediction, Project, Recommendation, RiskFactor


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from ml.src.config import (  # noqa: E402 - repository package is the integration boundary.
    CATEGORICAL_COLUMNS,
    FEATURE_COLUMNS,
    MODEL_VERSION,
    PROJECT_TYPES,
    SCENARIO_INTEGER_FEATURES,
    SCENARIO_PERCENTAGE_FEATURES,
    STATE_DISTRICTS,
    STAGE_NAMES,
)
from ml.src.pipeline import run_project_pipeline  # noqa: E402
from ml.src.what_if import simulate_scenario  # noqa: E402


def _json_number(value: Any) -> Any:
    """Normalize database Decimals without changing their ML meaning."""

    return float(value) if isinstance(value, Decimal) else value


def project_to_ml_input(project: Project) -> dict[str, Any]:
    """Build the canonical ML input from a stored project without duplicating its schema."""

    missing = [field for field in FEATURE_COLUMNS if getattr(project, field, None) is None]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": "Project is missing required ML inference fields", "fields": missing},
        )
    record = {field: _json_number(getattr(project, field)) for field in FEATURE_COLUMNS}
    record["project_id"] = str(project.id)
    validate_ml_input(record)
    return record


def validate_ml_input(record: Mapping[str, Any]) -> None:
    """Validate the application boundary using constants owned by the ML package."""

    missing = [field for field in FEATURE_COLUMNS if record.get(field) is None]
    if missing:
        raise ValueError(f"Missing required ML inference fields: {missing}")
    if record["project_type"] not in PROJECT_TYPES:
        raise ValueError(f"Invalid project_type: {record['project_type']}")
    if record["state"] not in STATE_DISTRICTS:
        raise ValueError(f"Invalid state: {record['state']}")
    if record["district"] not in STATE_DISTRICTS[record["state"]]:
        raise ValueError(f"district '{record['district']}' is not valid for state '{record['state']}'")
    if record["current_stage"] not in STAGE_NAMES:
        raise ValueError(f"Invalid current_stage: {record['current_stage']}")
    for feature in FEATURE_COLUMNS:
        value = record[feature]
        if feature in CATEGORICAL_COLUMNS:
            continue
        if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
            raise ValueError(f"{feature} must be numeric")
        number = float(value)
        if feature in SCENARIO_INTEGER_FEATURES and not number.is_integer():
            raise ValueError(f"{feature} must be an integer")
        if feature in SCENARIO_PERCENTAGE_FEATURES and not 0 <= number <= 100:
            raise ValueError(f"{feature} must be between 0 and 100")
        if feature == "historical_delay_rate" and not 0 <= number <= 1:
            raise ValueError("historical_delay_rate must be between 0 and 1")
        if feature != "days_remaining_to_target" and number < 0:
            raise ValueError(f"{feature} must not be negative")


def run_assessment(project: Project) -> dict[str, Any]:
    """Run the existing one-project pipeline and present its complete result unchanged."""

    try:
        return run_project_pipeline(project_to_ml_input(project))
    except HTTPException:
        raise
    except (ValueError, TypeError) as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error
    except Exception as error:  # Model/SHAP policy failures must not become opaque 500s.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ML assessment could not be completed. Verify the model artifact and ML dependencies.",
        ) from error


def persist_assessment(db: Session, project: Project, assessment: Mapping[str, Any]) -> Prediction:
    """Persist a pipeline result without touching manually created operational records."""

    prediction_data = assessment["prediction"]
    prediction = Prediction(
        project_id=project.id,
        risk_score=prediction_data["risk_score"],
        delay_probability=prediction_data["delay_probability"],
        predicted_delay_days=None,  # The ML package intentionally has no duration model.
        risk_category=prediction_data["risk_category"],
        model_version=MODEL_VERSION,
    )
    db.add(prediction)
    db.flush()
    officer_factors = assessment["explanation"]["officer_facing_factors"]
    for direction, factors in officer_factors.items():
        for factor in factors:
            db.add(RiskFactor(
                prediction_id=prediction.id,
                factor_name=factor["label"],
                impact=factor["shap_value"],
                direction=direction,
                rank=factor["rank"],
            ))

    # Only records explicitly created by this adapter are refreshed. Officer-maintained
    # recommendations and alerts remain untouched.
    for item in db.scalars(select(Recommendation).where(
        Recommendation.project_id == project.id, Recommendation.title.like("ML: %")
    )).all():
        db.delete(item)
    for item in db.scalars(select(Alert).where(
        Alert.project_id == project.id, Alert.alert_type.like("ML:%")
    )).all():
        db.delete(item)
    db.flush()

    for item in assessment["recommendations"]["recommendations"]:
        description = (
            f"Action: {item['action']}\nResponsible role: {item['responsible_role']}\n"
            f"Suggested deadline: {item['suggested_deadline_days']} days\nReason: {item['reason']}\n"
            f"Monitoring: {item['monitoring']}"
        )
        db.add(Recommendation(
            project_id=project.id, title=f"ML: {item['category']}", description=description,
            priority=item["priority"], status="Pending",
        ))
    for item in assessment["alerts"]:
        message = (
            f"{item['message']} Reason: {item['reason']} Escalation required: "
            f"{'yes' if item['escalation_required'] else 'no'}."
        )
        db.add(Alert(
            project_id=project.id, alert_type=f"ML:{item['category']}", severity=item["severity"], message=message,
        ))
    db.commit()
    db.refresh(prediction)
    return prediction


def run_what_if(project: Project, changes: Mapping[str, Any]) -> dict[str, Any]:
    """Execute the ML-owned What-If operation without persisting a scenario."""

    try:
        return simulate_scenario(project_to_ml_input(project), changes)
    except HTTPException:
        raise
    except (ValueError, TypeError) as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="What-If analysis could not be completed.") from error
