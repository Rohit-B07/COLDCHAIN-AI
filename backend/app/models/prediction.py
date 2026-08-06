"""Prediction model: temperature-excursion risk for a shipment."""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import JSON, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import TimestampMixin, uuid_pk

if TYPE_CHECKING:
    from app.models.shipment import Shipment


class Prediction(TimestampMixin, Base):
    __tablename__ = "predictions"

    id: Mapped[UUID] = uuid_pk()
    shipment_id: Mapped[UUID] = mapped_column(
        ForeignKey("shipments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    excursion_risk: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    risk_level: Mapped[str] = mapped_column(
        "risk_level", String(16), nullable=False, default="low"
    )
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    expected_min_temp: Mapped[float] = mapped_column(Float, nullable=False, default=2.0)
    expected_max_temp: Mapped[float] = mapped_column(Float, nullable=False, default=8.0)
    model_version: Mapped[str] = mapped_column(String(64), nullable=False, default="rule-based-v1")
    features: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    explanations: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    shipment: Mapped["Shipment"] = relationship(back_populates="predictions")
