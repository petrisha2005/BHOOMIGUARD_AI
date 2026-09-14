"""Prediction ORM model."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, text
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Prediction(Base):
    """Maps the existing predictions table."""

    __tablename__ = "predictions"

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    project_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    risk_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    delay_probability: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    predicted_delay_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    risk_category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    model_version: Mapped[str | None] = mapped_column(String(100), nullable=True)
    predicted_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=text("now()")
    )

    project: Mapped["Project"] = relationship(back_populates="predictions")
    risk_factors: Mapped[list["RiskFactor"]] = relationship(back_populates="prediction")
