"""Acquisition case management API routes."""

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import AcquisitionCase
from app.schemas.acquisition_case import AcquisitionCaseCreate, AcquisitionCaseResponse, AcquisitionCaseUpdate
from app.services.database import get_project_or_404


router = APIRouter(prefix="/cases", tags=["acquisition cases"])


def get_case_or_404(case_id: UUID, db: Session) -> AcquisitionCase:
    case = db.get(AcquisitionCase, case_id)
    if case is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Acquisition case not found")
    return case


@router.get("", response_model=list[AcquisitionCaseResponse])
def list_cases(
    project_id: UUID | None = None,
    case_status: str | None = None,
    search: str | None = Query(default=None, max_length=100),
    db: Session = Depends(get_db),
) -> list[AcquisitionCase]:
    statement = select(AcquisitionCase).order_by(AcquisitionCase.created_at.desc())
    if project_id:
        statement = statement.where(AcquisitionCase.project_id == project_id)
    if case_status:
        statement = statement.where(AcquisitionCase.case_status == case_status)
    if search:
        pattern = f"%{search.strip()}%"
        statement = statement.where(or_(AcquisitionCase.case_number.ilike(pattern), AcquisitionCase.village.ilike(pattern)))
    return list(db.scalars(statement).all())


@router.post("", response_model=AcquisitionCaseResponse, status_code=status.HTTP_201_CREATED)
def create_case(case_in: AcquisitionCaseCreate, db: Session = Depends(get_db)) -> AcquisitionCase:
    get_project_or_404(case_in.project_id, db)
    case = AcquisitionCase(**case_in.model_dump(exclude_unset=True))
    db.add(case)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=400, detail="Case could not be created with the supplied data") from error
    db.refresh(case)
    return case


@router.get("/{case_id}", response_model=AcquisitionCaseResponse)
def get_case(case_id: UUID, db: Session = Depends(get_db)) -> AcquisitionCase:
    return get_case_or_404(case_id, db)


@router.put("/{case_id}", response_model=AcquisitionCaseResponse)
def update_case(case_id: UUID, case_in: AcquisitionCaseUpdate, db: Session = Depends(get_db)) -> AcquisitionCase:
    changes = case_in.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status_code=400, detail="At least one field must be provided for update")
    case = get_case_or_404(case_id, db)
    for field, value in changes.items():
        setattr(case, field, value)
    case.updated_at = datetime.now(UTC).replace(tzinfo=None)
    db.commit()
    db.refresh(case)
    return case


@router.delete("/{case_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_case(case_id: UUID, db: Session = Depends(get_db)) -> Response:
    db.delete(get_case_or_404(case_id, db))
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
