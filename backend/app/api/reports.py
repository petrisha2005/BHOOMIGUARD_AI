"""PDF report download routes."""

import re
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.session import get_db
from app.models import Prediction, Project
from app.services.database import get_project_or_404
from app.services.report_generator import build_project_report


router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/projects/{project_id}", response_class=Response)
def download_project_report(project_id: UUID, db: Session = Depends(get_db)) -> Response:
    """Generate a report from live records without persisting a generated file."""

    project = db.scalar(
        select(Project)
        .where(Project.id == project_id)
        .options(
            selectinload(Project.acquisition_cases),
            selectinload(Project.predictions).selectinload(Prediction.risk_factors),
            selectinload(Project.recommendations),
            selectinload(Project.alerts),
            selectinload(Project.interventions),
        )
    )
    if project is None:
        get_project_or_404(project_id, db)
    predictions = sorted(project.predictions, key=lambda item: item.predicted_at, reverse=True)
    prediction = predictions[0] if predictions else None
    try:
        pdf = build_project_report(
            project,
            prediction,
            prediction.risk_factors if prediction else [],
            project.recommendations,
            project.alerts,
            project.interventions,
            project.acquisition_cases,
        )
    except RuntimeError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="PDF report generation dependencies are not installed",
        ) from error
    safe_project_code = re.sub(r"[^A-Za-z0-9._-]", "_", project.project_code)
    filename = f"bhoomiguard-{safe_project_code}.pdf"
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
