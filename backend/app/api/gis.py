"""GIS API routes providing persisted project locations."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.analytics import latest_predictions_by_project
from app.db.session import get_db
from app.models import Project
from app.schemas.analytics import MapProjectResponse


router = APIRouter(prefix="/gis", tags=["GIS"])


@router.get("/projects", response_model=list[MapProjectResponse])
def list_project_locations(db: Session = Depends(get_db)) -> list[MapProjectResponse]:
    """Return only projects with real latitude and longitude values."""

    projects = db.scalars(
        select(Project).where(Project.latitude.is_not(None), Project.longitude.is_not(None))
    ).all()
    latest_predictions = latest_predictions_by_project(db)
    return [
        MapProjectResponse(
            id=project.id,
            project_code=project.project_code,
            name=project.name,
            district=project.district,
            current_stage=project.current_stage,
            latitude=project.latitude,
            longitude=project.longitude,
            status=project.status,
            risk_category=latest_predictions[project.id].risk_category if project.id in latest_predictions else None,
            delay_probability=latest_predictions[project.id].delay_probability if project.id in latest_predictions else None,
        )
        for project in projects
    ]
