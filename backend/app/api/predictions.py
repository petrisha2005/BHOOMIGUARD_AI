"""Prediction read and Role 1 integration routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.session import get_db
from app.models import Prediction, RiskFactor
from app.schemas.prediction import PredictionWithFactorsResponse, RiskFactorResponse
from app.services.database import get_project_or_404
from app.services.ml_integration import persist_assessment, run_assessment, run_what_if


router = APIRouter(tags=["predictions"])


@router.get("/projects/{project_id}/predictions", response_model=list[PredictionWithFactorsResponse])
def list_project_predictions(project_id: UUID, db: Session = Depends(get_db)) -> list[Prediction]:
    get_project_or_404(project_id, db)
    return list(
        db.scalars(
            select(Prediction)
            .where(Prediction.project_id == project_id)
            .options(selectinload(Prediction.risk_factors))
            .order_by(Prediction.predicted_at.desc())
        ).all()
    )


@router.get("/predictions/{prediction_id}/risk-factors", response_model=list[RiskFactorResponse])
def list_risk_factors(prediction_id: UUID, db: Session = Depends(get_db)) -> list[RiskFactor]:
    prediction = db.get(Prediction, prediction_id)
    if prediction is None:
        raise HTTPException(status_code=404, detail="Prediction not found")
    return list(
        db.scalars(
            select(RiskFactor)
            .where(RiskFactor.prediction_id == prediction_id)
            .order_by(RiskFactor.rank.asc().nulls_last(), RiskFactor.impact.desc().nulls_last())
        ).all()
    )


@router.post("/projects/{project_id}/predictions/refresh", response_model=PredictionWithFactorsResponse, status_code=status.HTTP_201_CREATED)
def refresh_prediction(project_id: UUID, db: Session = Depends(get_db)) -> Prediction:
    """Run the local BhoomiGuard ML pipeline and persist its assessment."""

    project = get_project_or_404(project_id, db)
    prediction = persist_assessment(db, project, run_assessment(project))
    return db.scalar(select(Prediction).where(Prediction.id == prediction.id).options(selectinload(Prediction.risk_factors)))


@router.post("/projects/{project_id}/what-if")
def run_project_what_if(project_id: UUID, changes: dict[str, object], db: Session = Depends(get_db)) -> dict[str, object]:
    """Run a non-persistent scenario against the existing project's ML input."""

    return run_what_if(get_project_or_404(project_id, db), changes)
