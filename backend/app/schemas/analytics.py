"""Analytics, GIS and integration status schemas."""

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class DistributionItem(BaseModel):
    label: str
    value: int


class TrendItem(BaseModel):
    period: str
    value: int


class AnalyticsOverviewResponse(BaseModel):
    total_projects: int
    active_projects: int
    high_critical_risk_projects: int
    delayed_projects: int
    open_alerts: int
    active_cases: int
    projects_by_district: list[DistributionItem]
    risk_distribution: list[DistributionItem]
    status_distribution: list[DistributionItem]
    stage_distribution: list[DistributionItem]
    project_creation_trend: list[TrendItem]


class AttentionProjectResponse(BaseModel):
    id: UUID
    project_code: str
    name: str
    district: str | None
    current_stage: str | None
    status: str | None
    risk_category: str | None
    delay_probability: Decimal | None
    predicted_delay_days: int | None
    bottleneck: str | None


class MapProjectResponse(BaseModel):
    id: UUID
    project_code: str
    name: str
    district: str | None
    current_stage: str | None
    latitude: Decimal
    longitude: Decimal
    status: str | None
    risk_category: str | None
    delay_probability: Decimal | None


class IntegrationStatusResponse(BaseModel):
    ml_service_configured: bool
    copilot_service_configured: bool
