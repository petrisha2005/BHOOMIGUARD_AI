"""Analytics, GIS and integration status schemas."""

from decimal import Decimal
from uuid import UUID

from math import isfinite
from typing import Any

from pydantic import BaseModel, field_validator


def validate_linestring_geometry(value: dict[str, Any] | None) -> dict[str, Any] | None:
    """Validate the synthetic visual corridor as a GeoJSON LineString."""

    if value is None:
        return None
    if value.get("type") != "LineString":
        raise ValueError("corridor_geometry.type must be LineString")
    coordinates = value.get("coordinates")
    if not isinstance(coordinates, list) or len(coordinates) < 2:
        raise ValueError("corridor_geometry must contain at least two positions")
    for position in coordinates:
        if not isinstance(position, list) or len(position) != 2:
            raise ValueError("corridor positions must be [longitude, latitude]")
        try:
            longitude, latitude = float(position[0]), float(position[1])
        except (TypeError, ValueError) as error:
            raise ValueError("corridor coordinates must be numeric") from error
        if not isfinite(longitude) or not isfinite(latitude) or not -180 <= longitude <= 180 or not -90 <= latitude <= 90:
            raise ValueError("corridor coordinates are outside longitude/latitude bounds")
    return value


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
    corridor_geometry: dict[str, Any] | None = None

    @field_validator("corridor_geometry")
    @classmethod
    def corridor_is_linestring(cls, value: dict[str, Any] | None) -> dict[str, Any] | None:
        return validate_linestring_geometry(value)


class IntegrationStatusResponse(BaseModel):
    ml_service_configured: bool
    copilot_service_configured: bool
