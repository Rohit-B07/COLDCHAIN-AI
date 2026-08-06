"""Shipment model representing a cold-chain delivery order."""

import enum
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import TimestampMixin, uuid_pk

if TYPE_CHECKING:
    from app.models.logistics import ColdContainer
    from app.models.prediction import Prediction
    from app.models.route import Route


class ShipmentStatus(str, enum.Enum):
    CREATED = "created"
    PREDICTED = "predicted"
    DISPATCHED = "dispatched"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class Priority(str, enum.Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Shipment(TimestampMixin, Base):
    __tablename__ = "shipments"

    id: Mapped[UUID] = uuid_pk()
    tracking_code: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False
    )
    vaccine_name: Mapped[str] = mapped_column(String(255), nullable=False)
    dose_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    priority: Mapped[Priority] = mapped_column(
        String(16), nullable=False, default=Priority.MEDIUM.value
    )
    temperature_min: Mapped[Decimal] = mapped_column(Float, nullable=False, default=2.0)
    temperature_max: Mapped[Decimal] = mapped_column(Float, nullable=False, default=8.0)

    warehouse_id: Mapped[UUID] = mapped_column(
        ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    destination_id: Mapped[UUID] = mapped_column(
        ForeignKey("primary_health_centres.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    container_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("cold_containers.id", ondelete="SET NULL"), nullable=True, index=True
    )
    driver_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("drivers.id", ondelete="SET NULL"), nullable=True, index=True
    )

    status_state: Mapped[ShipmentStatus] = mapped_column(
        "status", String(24), nullable=False, default=ShipmentStatus.CREATED.value
    )
    dispatched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    estimated_delivery_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    predictions: Mapped[list["Prediction"]] = relationship(
        back_populates="shipment", cascade="all, delete-orphan"
    )
    routes: Mapped[list["Route"]] = relationship(
        back_populates="shipment", cascade="all, delete-orphan"
    )
    container: Mapped["ColdContainer | None"] = relationship(back_populates="shipments")
