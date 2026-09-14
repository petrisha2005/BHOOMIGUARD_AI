"""Recommendation schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.base import ORMResponse


class RecommendationCreate(BaseModel):
    project_id: UUID
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    priority: str | None = Field(default=None, max_length=50)
    status: str | None = Field(default=None, max_length=50)


class RecommendationUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    priority: str | None = Field(default=None, max_length=50)
    status: str | None = Field(default=None, max_length=50)


class RecommendationResponse(ORMResponse):
    id: UUID
    project_id: UUID
    title: str
    description: str | None
    priority: str | None
    status: str | None
    created_at: datetime
    updated_at: datetime
