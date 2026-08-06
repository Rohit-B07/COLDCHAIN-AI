"""Logistics assets: drivers, vehicles and cold containers."""

import enum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import TimestampMixin, uuid_pk

if TYPE_CHECKING:
    from app.models.shipment import Shipment


class DriverStatus(str, enum.Enum):
    AVAILABLE = "available"
    ASSIGNED = "assigned"
    ON_LEAVE = "on_leave"


class VehicleType(str, enum.Enum):
    REFRIGERATED_VAN = "refrigerated_van"
    REFRIGERATED_TRUCK = "refrigerated_truck"
    MOTORCYCLE_COOLER = "motorcycle_cooler"


class Driver(TimestampMixin, Base):
    __tablename__ = "drivers"
    __table_args__ = (
        CheckConstraint(
            "status IN ('available', 'assigned', 'on_leave')",
            name="ck_drivers_status",
        ),
        CheckConstraint("length(phone) BETWEEN 10 AND 15", name="ck_drivers_phone_length"),
    )

    id: Mapped[UUID] = uuid_pk()
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    phone: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    license_number: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[DriverStatus] = mapped_column(
        String(24), nullable=False, default=DriverStatus.AVAILABLE.value
    )
    vehicle_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("vehicles.id", ondelete="SET NULL"), nullable=True, index=True
    )

    vehicle: Mapped["Vehicle"] = relationship(  # noqa: F821
        "Vehicle", back_populates="driver", uselist=False
    )


class VehicleStatus(str, enum.Enum):
    ACTIVE = "active"
    MAINTENANCE = "maintenance"
    RETIRED = "retired"


class Vehicle(TimestampMixin, Base):
    __tablename__ = "vehicles"
    __table_args__ = (
        CheckConstraint("capacity_kg >= 0", name="ck_vehicles_capacity_kg"),
        CheckConstraint(
            "status IN ('active', 'maintenance', 'retired')",
            name="ck_vehicles_status",
        ),
        Index("ix_vehicles_type_status", "vehicle_type", "status"),
    )

    id: Mapped[UUID] = uuid_pk()
    registration_number: Mapped[str] = mapped_column(
        String(32), unique=True, index=True, nullable=False
    )
    vehicle_type: Mapped[VehicleType] = mapped_column(
        String(32), nullable=False, default=VehicleType.REFRIGERATED_VAN.value
    )
    capacity_kg: Mapped[int] = mapped_column(Integer, nullable=False, default=500)
    is_reefer: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    status: Mapped[VehicleStatus] = mapped_column(
        String(24), nullable=False, default=VehicleStatus.ACTIVE.value
    )

    driver: Mapped["Driver"] = relationship(  # noqa: F821
        "Driver", back_populates="vehicle", uselist=False
    )


class ContainerStatus(str, enum.Enum):
    IDLE = "idle"
    IN_TRANSIT = "in_transit"
    MAINTENANCE = "maintenance"


class ColdContainer(TimestampMixin, Base):
    __tablename__ = "cold_containers"

    id: Mapped[UUID] = uuid_pk()
    asset_tag: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    temperature_setpoint: Mapped[float] = mapped_column(Float, nullable=False, default=4.0)
    min_temperature: Mapped[float] = mapped_column(Float, nullable=False, default=2.0)
    max_temperature: Mapped[float] = mapped_column(Float, nullable=False, default=8.0)
    status: Mapped[str] = mapped_column(
        String(24), nullable=False, default=ContainerStatus.IDLE.value
    )
    current_latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    current_longitude: Mapped[float | None] = mapped_column(Float, nullable=True)

    shipments: Mapped[list["Shipment"]] = relationship(back_populates="container")
    battery_level: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
