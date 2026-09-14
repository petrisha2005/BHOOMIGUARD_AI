"""Acquisition case schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.base import ORMResponse


class AcquisitionCaseCreate(BaseModel):
    project_id: UUID
    case_number: str = Field(min_length=1, max_length=100)
    village: str | None = Field(default=None, max_length=255)
    current_stage: str | None = Field(default=None, max_length=100)
    case_status: str | None = Field(default=None, max_length=50)
    compensation_status: str | None = Field(default=None, max_length=100)
    dispute_status: str | None = Field(default=None, max_length=100)
    documentation_status: str | None = Field(default=None, max_length=100)
    days_pending: int | None = Field(default=None, ge=0)


class AcquisitionCaseUpdate(BaseModel):
    case_number: str | None = Field(default=None, min_length=1, max_length=100)
    village: str | None = Field(default=None, max_length=255)
    current_stage: str | None = Field(default=None, max_length=100)
    case_status: str | None = Field(default=None, max_length=50)
    compensation_status: str | None = Field(default=None, max_length=100)
    dispute_status: str | None = Field(default=None, max_length=100)
    documentation_status: str | None = Field(default=None, max_length=100)
    days_pending: int | None = Field(default=None, ge=0)


class AcquisitionCaseResponse(ORMResponse):
    id: UUID
    project_id: UUID
    case_number: str
    village: str | None
    current_stage: str | None
    case_status: str | None
    compensation_status: str | None
    dispute_status: str | None
    documentation_status: str | None
    days_pending: int | None
    created_at: datetime
    updated_at: datetime
