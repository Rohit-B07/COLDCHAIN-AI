"""Prediction model: temperature-excursion risk for a shipment."""

import enum
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import JSON, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import TimestampMixin, uuid_pk

if TYPE_CHECKING:
    from app.models.shipment import Shipment


class RiskLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Prediction(TimestampMixin, Base):
    __tablename__ = "predictions"

    id: Mapped[UUID] = uuid_pk()
    shipment_id: Mapped[UUID] = mapped_column(
        ForeignKey("shipments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    excursion_risk: Mapped[Decimal] = mapped_column(Float, nullable=False, default=0.0)
    risk_level: Mapped[RiskLevel] = mapped_column(
        String(16), nullable=False, default=RiskLevel.LOW.value
    )
    confidence: Mapped[Decimal] = mapped_column(Float, nullable=False, default=0.0)
    expected_min_temp: Mapped[Decimal] = mapped_column(Float, nullable=False, default=2.0)
    expected_max_temp: Mapped[Decimal] = mapped_column(Float, nullable=False, default=8.0)
    model_version: Mapped[str] = mapped_column(String(64), nullable=False, default="rule-based-v1")
    features: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    explanations: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    shipment: Mapped["Shipment"] = relationship(back_populates="predictions")
