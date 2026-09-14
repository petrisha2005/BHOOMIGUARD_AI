"""Acquisition case ORM model."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, String, text
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class AcquisitionCase(Base):
    """Maps the existing acquisition_cases table."""

    __tablename__ = "acquisition_cases"

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    project_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    case_number: Mapped[str] = mapped_column(String(100), nullable=False)
    village: Mapped[str | None] = mapped_column(String(255), nullable=True)
    current_stage: Mapped[str | None] = mapped_column(String(100), nullable=True)
    case_status: Mapped[str | None] = mapped_column(
        String(50), nullable=True, server_default=text("'Open'::character varying")
    )
    compensation_status: Mapped[str | None] = mapped_column(String(100), nullable=True)
    dispute_status: Mapped[str | None] = mapped_column(String(100), nullable=True)
    documentation_status: Mapped[str | None] = mapped_column(String(100), nullable=True)
    days_pending: Mapped[int | None] = mapped_column(
        Integer, nullable=True, server_default=text("0")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=text("now()")
    )

    project: Mapped["Project"] = relationship(back_populates="acquisition_cases")
