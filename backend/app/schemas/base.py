"""Shared Pydantic schema configuration."""

from pydantic import BaseModel, ConfigDict


class ORMResponse(BaseModel):
    """Base response type for SQLAlchemy ORM objects."""

    model_config = ConfigDict(from_attributes=True)
