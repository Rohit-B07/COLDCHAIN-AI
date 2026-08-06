"""Facility models: warehouses (origin) and primary health centres (destination)."""

import enum
from decimal import Decimal
from uuid import UUID

from sqlalchemy import CheckConstraint, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.base import TimestampMixin, uuid_pk


class PHStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class Warehouse(TimestampMixin, Base):
    __tablename__ = "warehouses"
    __table_args__ = (
        CheckConstraint("latitude BETWEEN -90 AND 90", name="ck_warehouses_latitude"),
        CheckConstraint("longitude BETWEEN -180 AND 180", name="ck_warehouses_longitude"),
        CheckConstraint("capacity >= 0", name="ck_warehouses_capacity"),
    )

    id: Mapped[UUID] = uuid_pk()
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    latitude: Mapped[Decimal] = mapped_column(Float, nullable=False)
    longitude: Mapped[Decimal] = mapped_column(Float, nullable=False)
    address: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class PrimaryHealthCentre(TimestampMixin, Base):
    __tablename__ = "primary_health_centres"
    __table_args__ = (
        CheckConstraint("latitude BETWEEN -90 AND 90", name="ck_phcs_latitude"),
        CheckConstraint("longitude BETWEEN -180 AND 180", name="ck_phcs_longitude"),
        CheckConstraint("capacity >= 0", name="ck_phcs_capacity"),
        CheckConstraint("priority_level BETWEEN 1 AND 10", name="ck_phcs_priority_level"),
    )

    id: Mapped[UUID] = uuid_pk()
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    district: Mapped[str] = mapped_column(String(128), nullable=False)
    state: Mapped[str] = mapped_column(String(128), nullable=False)
    latitude: Mapped[Decimal] = mapped_column(Float, nullable=False)
    longitude: Mapped[Decimal] = mapped_column(Float, nullable=False)
    contact: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    priority_level: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(String(16), default=PHStatus.ACTIVE.value, nullable=False)
