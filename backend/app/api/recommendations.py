"""Recommendation API routes."""

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Recommendation
from app.schemas.recommendation import RecommendationCreate, RecommendationResponse, RecommendationUpdate
from app.services.database import get_project_or_404


router = APIRouter(prefix="/recommendations", tags=["recommendations"])


def get_recommendation_or_404(recommendation_id: UUID, db: Session) -> Recommendation:
    item = db.get(Recommendation, recommendation_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    return item


@router.get("", response_model=list[RecommendationResponse])
def list_recommendations(project_id: UUID | None = None, db: Session = Depends(get_db)) -> list[Recommendation]:
    statement = select(Recommendation).order_by(Recommendation.created_at.desc())
    if project_id:
        statement = statement.where(Recommendation.project_id == project_id)
    return list(db.scalars(statement).all())


@router.post("", response_model=RecommendationResponse, status_code=status.HTTP_201_CREATED)
def create_recommendation(item_in: RecommendationCreate, db: Session = Depends(get_db)) -> Recommendation:
    get_project_or_404(item_in.project_id, db)
    item = Recommendation(**item_in.model_dump(exclude_unset=True))
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/{recommendation_id}", response_model=RecommendationResponse)
def update_recommendation(recommendation_id: UUID, item_in: RecommendationUpdate, db: Session = Depends(get_db)) -> Recommendation:
    changes = item_in.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status_code=400, detail="At least one field must be provided for update")
    item = get_recommendation_or_404(recommendation_id, db)
    for field, value in changes.items():
        setattr(item, field, value)
    item.updated_at = datetime.now(UTC).replace(tzinfo=None)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{recommendation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_recommendation(recommendation_id: UUID, db: Session = Depends(get_db)) -> Response:
    db.delete(get_recommendation_or_404(recommendation_id, db))
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
