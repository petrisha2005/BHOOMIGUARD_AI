"""Prediction and risk factor schemas."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.base import ORMResponse


class RiskFactorResponse(ORMResponse):
    id: UUID
    prediction_id: UUID
    factor_name: str
    impact: Decimal | None
    direction: str | None
    rank: int | None
    created_at: datetime


class PredictionResponse(ORMResponse):
    id: UUID
    project_id: UUID
    risk_score: Decimal | None
    delay_probability: Decimal | None
    predicted_delay_days: int | None
    risk_category: str | None
    model_version: str | None
    predicted_at: datetime


class PredictionWithFactorsResponse(PredictionResponse):
    risk_factors: list[RiskFactorResponse] = []


class MLFactor(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    impact: Decimal | None = None
    direction: str | None = Field(default=None, max_length=50)
    rank: int | None = Field(default=None, ge=1)


class MLResponse(BaseModel):
    risk_score: Decimal | None = None
    delay_probability: Decimal | None = Field(default=None, ge=0, le=1)
    predicted_delay_days: int | None = Field(default=None, ge=0)
    risk_category: str | None = Field(default=None, max_length=50)
    model_version: str | None = Field(default=None, max_length=100)
    top_factors: list[MLFactor] = []
