"""Risk factor ORM model."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, text
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class RiskFactor(Base):
    """Maps the existing risk_factors table."""

    __tablename__ = "risk_factors"

    id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    prediction_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("predictions.id", ondelete="CASCADE"), nullable=False
    )
    factor_name: Mapped[str] = mapped_column(String(255), nullable=False)
    impact: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), nullable=True)
    direction: Mapped[str | None] = mapped_column(String(50), nullable=True)
    rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=text("now()")
    )

    prediction: Mapped["Prediction"] = relationship(back_populates="risk_factors")
