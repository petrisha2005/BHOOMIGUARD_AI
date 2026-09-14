"""Intervention schemas."""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.base import ORMResponse


class InterventionCreate(BaseModel):
    project_id: UUID
    intervention_type: str | None = Field(default=None, max_length=100)
    action: str = Field(min_length=1)
    owner_role: str | None = Field(default=None, max_length=100)
    status: str | None = Field(default=None, max_length=50)
    due_date: date | None = None
    notes: str | None = None


class InterventionUpdate(BaseModel):
    intervention_type: str | None = Field(default=None, max_length=100)
    action: str | None = Field(default=None, min_length=1)
    owner_role: str | None = Field(default=None, max_length=100)
    status: str | None = Field(default=None, max_length=50)
    due_date: date | None = None
    notes: str | None = None


class InterventionResponse(ORMResponse):
    id: UUID
    project_id: UUID
    intervention_type: str | None
    action: str
    owner_role: str | None
    status: str | None
    due_date: date | None
    notes: str | None
    created_at: datetime
    updated_at: datetime
