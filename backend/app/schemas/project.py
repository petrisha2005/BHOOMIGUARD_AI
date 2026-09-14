"""Pydantic schemas for Project API requests and responses."""

from datetime import datetime
from decimal import Decimal
from typing import Annotated, Any
from uuid import UUID

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from app.schemas.acquisition_case import AcquisitionCaseResponse
from app.schemas.alert import AlertResponse
from app.schemas.intervention import InterventionResponse
from app.schemas.prediction import PredictionWithFactorsResponse
from app.schemas.recommendation import RecommendationResponse


LandArea = Annotated[Decimal, Field(ge=0, max_digits=12, decimal_places=2)]
Percentage = Annotated[Decimal, Field(ge=0, le=100, max_digits=5, decimal_places=2)]
Count = Annotated[int, Field(ge=0)]
DelayDays = Annotated[int, Field(ge=0)]
HistoricalDelayRate = Annotated[Decimal, Field(ge=0, max_digits=10, decimal_places=4)]
Latitude = Annotated[Decimal, Field(ge=-90, le=90, max_digits=10, decimal_places=7)]
Longitude = Annotated[Decimal, Field(ge=-180, le=180, max_digits=10, decimal_places=7)]


class ProjectCreate(BaseModel):
    """Payload for creating a project."""

    project_code: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=255)
    project_type: str | None = Field(default=None, max_length=100)
    state: str | None = Field(default=None, max_length=100)
    district: str | None = Field(default=None, max_length=100)
    village: str | None = Field(default=None, max_length=255)
    land_area_acres: LandArea | None = None
    affected_families: Count | None = None
    villages_affected: Count | None = None
    legal_disputes: Count | None = None
    ownership_conflicts: Count | None = None
    pending_court_cases: Count | None = None
    documentation_completion_pct: Percentage | None = Field(
        default=None,
        validation_alias=AliasChoices("documentation_completion_pct", "documentation_percent"),
    )
    missing_documents: Count | None = None
    compensation_completion_pct: Percentage | None = Field(
        default=None,
        validation_alias=AliasChoices("compensation_completion_pct", "compensation_percent"),
    )
    compensation_pending_cases: Count | None = None
    average_compensation_delay_days: DelayDays | None = None
    rehabilitation_completion_pct: Percentage | None = Field(
        default=None,
        validation_alias=AliasChoices("rehabilitation_completion_pct", "rehabilitation_percent"),
    )
    resettlement_completion_pct: Percentage | None = None
    affected_families_rehabilitated: Count | None = None
    pending_approvals: Count | None = None
    approval_delay_days: DelayDays | None = None
    stakeholder_response_delay_days: DelayDays | None = None
    current_stage: str | None = Field(default=None, max_length=100)
    days_in_current_stage: DelayDays | None = None
    possession_completion_pct: Percentage | None = Field(
        default=None,
        validation_alias=AliasChoices("possession_completion_pct", "possession_percent"),
    )
    historical_delay_rate: HistoricalDelayRate | None = None
    days_remaining_to_target: int | None = None
    previous_stage_delay_days: DelayDays | None = None
    status: str | None = Field(default=None, max_length=50)
    latitude: Latitude | None = None
    longitude: Longitude | None = None


class ProjectUpdate(BaseModel):
    """Payload for partially updating an existing project."""

    project_code: str | None = Field(default=None, min_length=1, max_length=50)
    name: str | None = Field(default=None, min_length=1, max_length=255)
    project_type: str | None = Field(default=None, max_length=100)
    state: str | None = Field(default=None, max_length=100)
    district: str | None = Field(default=None, max_length=100)
    village: str | None = Field(default=None, max_length=255)
    land_area_acres: LandArea | None = None
    affected_families: Count | None = None
    villages_affected: Count | None = None
    legal_disputes: Count | None = None
    ownership_conflicts: Count | None = None
    pending_court_cases: Count | None = None
    documentation_completion_pct: Percentage | None = Field(
        default=None,
        validation_alias=AliasChoices("documentation_completion_pct", "documentation_percent"),
    )
    missing_documents: Count | None = None
    compensation_completion_pct: Percentage | None = Field(
        default=None,
        validation_alias=AliasChoices("compensation_completion_pct", "compensation_percent"),
    )
    compensation_pending_cases: Count | None = None
    average_compensation_delay_days: DelayDays | None = None
    rehabilitation_completion_pct: Percentage | None = Field(
        default=None,
        validation_alias=AliasChoices("rehabilitation_completion_pct", "rehabilitation_percent"),
    )
    resettlement_completion_pct: Percentage | None = None
    affected_families_rehabilitated: Count | None = None
    pending_approvals: Count | None = None
    approval_delay_days: DelayDays | None = None
    stakeholder_response_delay_days: DelayDays | None = None
    current_stage: str | None = Field(default=None, max_length=100)
    days_in_current_stage: DelayDays | None = None
    possession_completion_pct: Percentage | None = Field(
        default=None,
        validation_alias=AliasChoices("possession_completion_pct", "possession_percent"),
    )
    historical_delay_rate: HistoricalDelayRate | None = None
    days_remaining_to_target: int | None = None
    previous_stage_delay_days: DelayDays | None = None
    status: str | None = Field(default=None, max_length=50)
    latitude: Latitude | None = None
    longitude: Longitude | None = None


class ProjectResponse(BaseModel):
    """Project data returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_code: str
    name: str
    project_type: str | None
    state: str | None
    district: str | None
    village: str | None
    land_area_acres: Decimal | None
    affected_families: int | None
    villages_affected: int | None
    pending_court_cases: int | None
    documentation_completion_pct: Decimal | None
    missing_documents: int | None
    compensation_completion_pct: Decimal | None
    compensation_pending_cases: int | None
    average_compensation_delay_days: int | None
    rehabilitation_completion_pct: Decimal | None
    resettlement_completion_pct: Decimal | None
    affected_families_rehabilitated: int | None
    documentation_percent: Decimal | None
    compensation_percent: Decimal | None
    legal_disputes: int | None
    ownership_conflicts: int | None
    pending_approvals: int | None
    rehabilitation_percent: Decimal | None
    possession_percent: Decimal | None
    approval_delay_days: int | None
    stakeholder_response_delay_days: int | None
    current_stage: str | None
    days_in_current_stage: int | None
    possession_completion_pct: Decimal | None
    historical_delay_rate: Decimal | None
    days_remaining_to_target: int | None
    previous_stage_delay_days: int | None
    status: str | None
    latitude: Decimal | None
    longitude: Decimal | None
    created_at: datetime
    updated_at: datetime


class ProjectDetailResponse(BaseModel):
    """Project information enriched from its existing related tables."""

    project: ProjectResponse
    acquisition_cases: list[AcquisitionCaseResponse]
    latest_prediction: PredictionWithFactorsResponse | None
    recommendations: list[RecommendationResponse]
    alerts: list[AlertResponse]
    interventions: list[InterventionResponse]


class ProjectImportRowError(BaseModel):
    """One CSV row validation problem, reported without exposing server internals."""

    row_number: int
    field: str
    message: str


class ProjectImportRequest(BaseModel):
    """Parsed CSV rows supplied by the officer-facing upload workflow."""

    rows: list[dict[str, Any]] = Field(min_length=1, max_length=500)


class ProjectImportPreviewResponse(BaseModel):
    valid_rows: int
    invalid_rows: int
    errors: list[ProjectImportRowError]
    preview: list[ProjectCreate]


class ProjectImportResult(BaseModel):
    created_count: int
