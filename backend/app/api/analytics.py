"""Read-only analytics endpoints built from live project data."""

from collections import Counter
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.session import get_db
from app.models import AcquisitionCase, Alert, Prediction, Project
from app.schemas.analytics import AnalyticsOverviewResponse, AttentionProjectResponse, DistributionItem, TrendItem


router = APIRouter(prefix="/analytics", tags=["analytics"])

DELAYED_STATUSES = {"delayed", "on hold", "stalled"}
ATTENTION_RISKS = {"high", "critical"}


def normalized(value: object | None) -> str:
    return str(value or "").strip().lower()


def latest_predictions_by_project(db: Session) -> dict[object, Prediction]:
    predictions = db.scalars(select(Prediction).options(selectinload(Prediction.risk_factors))).all()
    latest: dict[object, Prediction] = {}
    for prediction in predictions:
        current = latest.get(prediction.project_id)
        if current is None or prediction.predicted_at > current.predicted_at:
            latest[prediction.project_id] = prediction
    return latest


def distribution(counter: Counter[str]) -> list[DistributionItem]:
    return [DistributionItem(label=label, value=value) for label, value in sorted(counter.items())]


def bottleneck_for(project: Project, prediction: Prediction | None) -> str | None:
    if prediction and prediction.risk_factors:
        top_factor = sorted(
            prediction.risk_factors,
            key=lambda factor: (factor.rank is None, factor.rank or 0, -(float(factor.impact or 0))),
        )[0]
        return top_factor.factor_name
    if (project.legal_disputes or 0) > 0:
        return "Legal disputes"
    if (project.ownership_conflicts or 0) > 0:
        return "Ownership conflicts"
    if (project.pending_approvals or 0) > 0:
        return "Pending approvals"
    return None


@router.get("/overview", response_model=AnalyticsOverviewResponse)
def get_overview(db: Session = Depends(get_db)) -> AnalyticsOverviewResponse:
    """Return real project, status, prediction, district and stage metrics."""

    projects = list(db.scalars(select(Project)).all())
    cases = list(db.scalars(select(AcquisitionCase)).all())
    latest_predictions = latest_predictions_by_project(db)
    status_counts = Counter(str(project.status or "Unspecified") for project in projects)
    district_counts = Counter(str(project.district or "Unspecified") for project in projects)
    stage_counts = Counter(str(project.current_stage or "Unspecified") for project in projects)
    risk_counts = Counter(
        str(prediction.risk_category)
        for prediction in latest_predictions.values()
        if prediction.risk_category
    )
    month_counts = Counter(
        project.created_at.strftime("%Y-%m")
        for project in projects
        if isinstance(project.created_at, datetime)
    )
    high_critical = sum(
        1 for prediction in latest_predictions.values() if normalized(prediction.risk_category) in ATTENTION_RISKS
    )
    return AnalyticsOverviewResponse(
        total_projects=len(projects),
        active_projects=sum(1 for project in projects if normalized(project.status) == "active"),
        high_critical_risk_projects=high_critical,
        delayed_projects=sum(1 for project in projects if normalized(project.status) in DELAYED_STATUSES),
        open_alerts=sum(1 for alert in db.scalars(select(Alert)).all() if not alert.acknowledged),
        active_cases=sum(
            1 for case in cases if normalized(case.case_status) in {"open", "active", "in progress"}
        ),
        projects_by_district=distribution(district_counts),
        risk_distribution=distribution(risk_counts),
        status_distribution=distribution(status_counts),
        stage_distribution=distribution(stage_counts),
        project_creation_trend=[TrendItem(period=period, value=value) for period, value in sorted(month_counts.items())],
    )


@router.get("/attention", response_model=list[AttentionProjectResponse])
def get_projects_requiring_attention(db: Session = Depends(get_db)) -> list[AttentionProjectResponse]:
    """Return projects with a persisted high-risk signal or delay condition."""

    projects = list(db.scalars(select(Project)).all())
    latest_predictions = latest_predictions_by_project(db)
    items: list[AttentionProjectResponse] = []
    for project in projects:
        prediction = latest_predictions.get(project.id)
        has_prediction_risk = prediction and normalized(prediction.risk_category) in ATTENTION_RISKS
        has_delay = normalized(project.status) in DELAYED_STATUSES
        has_operational_bottleneck = (project.legal_disputes or 0) > 0 or (project.ownership_conflicts or 0) > 0 or (project.pending_approvals or 0) > 0
        if not (has_prediction_risk or has_delay or has_operational_bottleneck):
            continue
        items.append(AttentionProjectResponse(
            id=project.id,
            project_code=project.project_code,
            name=project.name,
            district=project.district,
            current_stage=project.current_stage,
            status=project.status,
            risk_category=prediction.risk_category if prediction else None,
            delay_probability=prediction.delay_probability if prediction else None,
            predicted_delay_days=prediction.predicted_delay_days if prediction else None,
            bottleneck=bottleneck_for(project, prediction),
        ))
    risk_order = {"critical": 0, "high": 1, "medium": 2}
    return sorted(items, key=lambda item: risk_order.get(normalized(item.risk_category), 3))
