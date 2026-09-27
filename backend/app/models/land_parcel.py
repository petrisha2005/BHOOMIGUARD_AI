"""Persistent synthetic/demo parcel geometry linked to a BhoomiGuard project."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Numeric, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class LandParcel(Base):
    """A prototype parcel with synthetic GeoJSON Polygon geometry.

    Geometry is deliberately JSONB rather than PostGIS.  It represents development
    demo boundaries only and must never be presented as cadastral data.
    """

    __tablename__ = "land_parcels"
    __table_args__ = (UniqueConstraint("project_id", "parcel_id", name="uq_land_parcels_project_parcel"),)

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    project_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    parcel_id: Mapped[str] = mapped_column(String(100), nullable=False)
    ownership_type: Mapped[str] = mapped_column(String(20), nullable=False)
    acquisition_status: Mapped[str] = mapped_column(String(20), nullable=False)
    area_acres: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    geometry: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=text("now()")
    )

    project: Mapped["Project"] = relationship(back_populates="land_parcels")
    acquisition_cases: Mapped[list["AcquisitionCase"]] = relationship(back_populates="land_parcel")
