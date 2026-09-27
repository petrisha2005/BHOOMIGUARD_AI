"""Schemas for prototype parcel GIS responses and GeoJSON validation."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from math import isfinite
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


OwnershipType = Literal["GOVERNMENT", "PRIVATE"]
AcquisitionStatus = Literal["NOT_STARTED", "IN_PROGRESS", "ACQUIRED", "DISPUTED", "ON_HOLD"]


def validate_polygon_geometry(value: dict[str, Any]) -> dict[str, Any]:
    """Accept only closed GeoJSON Polygon rings with valid longitude/latitude pairs."""

    if value.get("type") != "Polygon":
        raise ValueError("geometry.type must be Polygon")
    coordinates = value.get("coordinates")
    if not isinstance(coordinates, list) or not coordinates:
        raise ValueError("geometry.coordinates must contain at least one polygon ring")
    for ring in coordinates:
        if not isinstance(ring, list) or len(ring) < 4:
            raise ValueError("each polygon ring must contain at least four positions")
        normalized: list[tuple[float, float]] = []
        for position in ring:
            if not isinstance(position, list) or len(position) != 2:
                raise ValueError("each polygon position must be [longitude, latitude]")
            longitude, latitude = position
            if isinstance(longitude, bool) or isinstance(latitude, bool):
                raise ValueError("polygon coordinates must be numeric")
            try:
                longitude_float, latitude_float = float(longitude), float(latitude)
            except (TypeError, ValueError) as error:
                raise ValueError("polygon coordinates must be numeric") from error
            if not isfinite(longitude_float) or not isfinite(latitude_float):
                raise ValueError("polygon coordinates must be finite")
            if not -180 <= longitude_float <= 180 or not -90 <= latitude_float <= 90:
                raise ValueError("polygon coordinates are outside longitude/latitude bounds")
            normalized.append((longitude_float, latitude_float))
        if normalized[0] != normalized[-1]:
            raise ValueError("each polygon ring must be closed")
    return value


class ParcelProjectRiskResponse(BaseModel):
    """Latest project-level risk shown for context, never a parcel ML prediction."""

    risk_score: Decimal | None
    delay_probability: Decimal | None
    risk_category: str | None


class LandParcelResponse(BaseModel):
    id: UUID
    project_id: UUID
    parcel_id: str
    ownership_type: OwnershipType
    acquisition_status: AcquisitionStatus
    area_acres: Decimal = Field(gt=0)
    geometry: dict[str, Any]
    acquisition_case_id: UUID | None = None
    latest_project_risk: ParcelProjectRiskResponse | None = None
    created_at: datetime
    updated_at: datetime

    @field_validator("geometry")
    @classmethod
    def geometry_is_polygon(cls, value: dict[str, Any]) -> dict[str, Any]:
        return validate_polygon_geometry(value)
