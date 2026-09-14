"""Intervention tracking API routes."""

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Intervention
from app.schemas.intervention import InterventionCreate, InterventionResponse, InterventionUpdate
from app.services.database import get_project_or_404


router = APIRouter(prefix="/interventions", tags=["interventions"])


def get_intervention_or_404(intervention_id: UUID, db: Session) -> Intervention:
    item = db.get(Intervention, intervention_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Intervention not found")
    return item


@router.get("", response_model=list[InterventionResponse])
def list_interventions(project_id: UUID | None = None, db: Session = Depends(get_db)) -> list[Intervention]:
    statement = select(Intervention).order_by(Intervention.created_at.desc())
    if project_id:
        statement = statement.where(Intervention.project_id == project_id)
    return list(db.scalars(statement).all())


@router.post("", response_model=InterventionResponse, status_code=status.HTTP_201_CREATED)
def create_intervention(item_in: InterventionCreate, db: Session = Depends(get_db)) -> Intervention:
    get_project_or_404(item_in.project_id, db)
    item = Intervention(**item_in.model_dump(exclude_unset=True))
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/{intervention_id}", response_model=InterventionResponse)
def get_intervention(intervention_id: UUID, db: Session = Depends(get_db)) -> Intervention:
    return get_intervention_or_404(intervention_id, db)


@router.put("/{intervention_id}", response_model=InterventionResponse)
def update_intervention(intervention_id: UUID, item_in: InterventionUpdate, db: Session = Depends(get_db)) -> Intervention:
    changes = item_in.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status_code=400, detail="At least one field must be provided for update")
    item = get_intervention_or_404(intervention_id, db)
    for field, value in changes.items():
        setattr(item, field, value)
    item.updated_at = datetime.now(UTC).replace(tzinfo=None)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{intervention_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_intervention(intervention_id: UUID, db: Session = Depends(get_db)) -> Response:
    db.delete(get_intervention_or_404(intervention_id, db))
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
