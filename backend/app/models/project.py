"""Project ORM model."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import DateTime, Integer, Numeric, String, text
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Project(Base):
    """Maps the existing projects table."""

    __tablename__ = "projects"

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    project_code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    project_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    district: Mapped[str | None] = mapped_column(String(100), nullable=True)
    village: Mapped[str | None] = mapped_column(String(255), nullable=True)
    land_area_acres: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    affected_families: Mapped[int | None] = mapped_column(
        Integer, nullable=True, server_default=text("0")
    )
    legal_disputes: Mapped[int | None] = mapped_column(
        Integer, nullable=True, server_default=text("0")
    )
    ownership_conflicts: Mapped[int | None] = mapped_column(
        Integer, nullable=True, server_default=text("0")
    )
    villages_affected: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pending_court_cases: Mapped[int | None] = mapped_column(Integer, nullable=True)
    documentation_completion_pct: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    missing_documents: Mapped[int | None] = mapped_column(Integer, nullable=True)
    compensation_completion_pct: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    compensation_pending_cases: Mapped[int | None] = mapped_column(Integer, nullable=True)
    average_compensation_delay_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rehabilitation_completion_pct: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    resettlement_completion_pct: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    affected_families_rehabilitated: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pending_approvals: Mapped[int | None] = mapped_column(
        Integer, nullable=True, server_default=text("0")
    )
    approval_delay_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    stakeholder_response_delay_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    current_stage: Mapped[str | None] = mapped_column(String(100), nullable=True)
    days_in_current_stage: Mapped[int | None] = mapped_column(
        Integer, nullable=True, server_default=text("0")
    )
    possession_completion_pct: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    historical_delay_rate: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    days_remaining_to_target: Mapped[int | None] = mapped_column(Integer, nullable=True)
    previous_stage_delay_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str | None] = mapped_column(
        String(50), nullable=True, server_default=text("'Active'::character varying")
    )
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 7), nullable=True)
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 7), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=text("now()")
    )

    acquisition_cases: Mapped[list["AcquisitionCase"]] = relationship(back_populates="project")
    predictions: Mapped[list["Prediction"]] = relationship(back_populates="project")
    recommendations: Mapped[list["Recommendation"]] = relationship(back_populates="project")
    alerts: Mapped[list["Alert"]] = relationship(back_populates="project")
    interventions: Mapped[list["Intervention"]] = relationship(back_populates="project")

    # Legacy API/report aliases retained while callers migrate to canonical ML names.
    @property
    def documentation_percent(self) -> Decimal | None:
        return self.documentation_completion_pct

    @documentation_percent.setter
    def documentation_percent(self, value: Decimal | None) -> None:
        self.documentation_completion_pct = value

    @property
    def compensation_percent(self) -> Decimal | None:
        return self.compensation_completion_pct

    @compensation_percent.setter
    def compensation_percent(self, value: Decimal | None) -> None:
        self.compensation_completion_pct = value

    @property
    def rehabilitation_percent(self) -> Decimal | None:
        return self.rehabilitation_completion_pct

    @rehabilitation_percent.setter
    def rehabilitation_percent(self, value: Decimal | None) -> None:
        self.rehabilitation_completion_pct = value

    @property
    def possession_percent(self) -> Decimal | None:
        return self.possession_completion_pct

    @possession_percent.setter
    def possession_percent(self, value: Decimal | None) -> None:
        self.possession_completion_pct = value
