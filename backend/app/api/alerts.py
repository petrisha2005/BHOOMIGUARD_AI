"""Alert center API routes."""

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Alert
from app.schemas.alert import AlertCreate, AlertResponse
from app.services.database import get_project_or_404


router = APIRouter(prefix="/alerts", tags=["alerts"])


def get_alert_or_404(alert_id: UUID, db: Session) -> Alert:
    alert = db.get(Alert, alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.get("", response_model=list[AlertResponse])
def list_alerts(
    project_id: UUID | None = None,
    severity: str | None = None,
    acknowledged: bool | None = None,
    db: Session = Depends(get_db),
) -> list[Alert]:
    statement = select(Alert).order_by(Alert.created_at.desc())
    if project_id:
        statement = statement.where(Alert.project_id == project_id)
    if severity:
        statement = statement.where(Alert.severity == severity)
    if acknowledged is not None:
        statement = statement.where(Alert.acknowledged == acknowledged)
    return list(db.scalars(statement).all())


@router.post("", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
def create_alert(alert_in: AlertCreate, db: Session = Depends(get_db)) -> Alert:
    get_project_or_404(alert_in.project_id, db)
    alert = Alert(**alert_in.model_dump(exclude_unset=True))
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


@router.put("/{alert_id}/acknowledge", response_model=AlertResponse)
def acknowledge_alert(alert_id: UUID, db: Session = Depends(get_db)) -> Alert:
    alert = get_alert_or_404(alert_id, db)
    if not alert.acknowledged:
        alert.acknowledged = True
        alert.acknowledged_at = datetime.now(UTC).replace(tzinfo=None)
        db.commit()
        db.refresh(alert)
    return alert
