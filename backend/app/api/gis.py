"""GIS API routes providing persisted project locations."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.analytics import latest_predictions_by_project
from app.db.session import get_db
from app.models import LandParcel, Project
from app.schemas.analytics import MapProjectResponse
from app.schemas.land_parcel import LandParcelResponse, ParcelProjectRiskResponse


router = APIRouter(prefix="/gis", tags=["GIS"])


def parcel_response(parcel: LandParcel, latest_prediction) -> LandParcelResponse:
    """Present prototype parcel geometry with optional linked project-level risk."""

    linked_case_id = parcel.acquisition_cases[0].id if parcel.acquisition_cases else None
    risk = None if latest_prediction is None else ParcelProjectRiskResponse(
        risk_score=latest_prediction.risk_score,
        delay_probability=latest_prediction.delay_probability,
        risk_category=latest_prediction.risk_category,
    )
    return LandParcelResponse(
        id=parcel.id,
        project_id=parcel.project_id,
        parcel_id=parcel.parcel_id,
        ownership_type=parcel.ownership_type,
        acquisition_status=parcel.acquisition_status,
        area_acres=parcel.area_acres,
        geometry=parcel.geometry,
        acquisition_case_id=linked_case_id,
        latest_project_risk=risk,
        created_at=parcel.created_at,
        updated_at=parcel.updated_at,
    )


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
            corridor_geometry=project.corridor_geometry,
        )
        for project in projects
    ]


@router.get("/parcels", response_model=list[LandParcelResponse])
def list_project_parcels(
    project_id: UUID = Query(...), db: Session = Depends(get_db)
) -> list[LandParcelResponse]:
    """Return synthetic/demo parcels for one existing project and its latest project risk."""

    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    parcels = db.scalars(
        select(LandParcel).where(LandParcel.project_id == project_id).order_by(LandParcel.parcel_id)
    ).all()
    latest_prediction = latest_predictions_by_project(db).get(project_id)
    return [parcel_response(parcel, latest_prediction) for parcel in parcels]


@router.get("/parcels/{parcel_id}", response_model=LandParcelResponse)
def get_parcel(parcel_id: UUID, db: Session = Depends(get_db)) -> LandParcelResponse:
    """Return one synthetic/demo parcel and its parent project's latest risk context."""

    parcel = db.get(LandParcel, parcel_id)
    if parcel is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Land parcel not found")
    return parcel_response(parcel, latest_predictions_by_project(db).get(parcel.project_id))
