"""Alert schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.base import ORMResponse


class AlertCreate(BaseModel):
    project_id: UUID
    alert_type: str | None = Field(default=None, max_length=100)
    severity: str | None = Field(default=None, max_length=50)
    message: str = Field(min_length=1)


class AlertResponse(ORMResponse):
    id: UUID
    project_id: UUID
    alert_type: str | None
    severity: str | None
    message: str
    acknowledged: bool
    acknowledged_at: datetime | None
    created_at: datetime
