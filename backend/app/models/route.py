"""Route model: planned delivery geometry and scoring per shipment."""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import TimestampMixin, uuid_pk

if TYPE_CHECKING:
    from app.models.shipment import Shipment


class Route(TimestampMixin, Base):
    __tablename__ = "routes"
    __table_args__ = (
        CheckConstraint("distance_km >= 0", name="ck_routes_distance_km"),
        CheckConstraint("duration_minutes >= 0", name="ck_routes_duration_minutes"),
        CheckConstraint("weather_factor > 0", name="ck_routes_weather_factor"),
        CheckConstraint("safety_score BETWEEN 0 AND 100", name="ck_routes_safety_score"),
    )

    id: Mapped[UUID] = uuid_pk()
    shipment_id: Mapped[UUID] = mapped_column(
        ForeignKey("shipments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    distance_km: Mapped[Decimal] = mapped_column(Float, nullable=False, default=0.0)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    stops: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    polyline: Mapped[str] = mapped_column(String(1000), nullable=False, default="")
    weather_factor: Mapped[Decimal] = mapped_column(Float, nullable=False, default=1.0)
    safety_score: Mapped[Decimal] = mapped_column(Float, nullable=False, default=0.0)
    is_selected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    shipment: Mapped["Shipment"] = relationship(back_populates="routes")
    waypoints: Mapped[list["Waypoint"]] = relationship(
        back_populates="route", cascade="all, delete-orphan", order_by="Waypoint.sequence"
    )


class Waypoint(TimestampMixin, Base):
    """A single stop along a planned route."""

    __tablename__ = "waypoints"
    __table_args__ = (
        UniqueConstraint("route_id", "sequence", name="uq_waypoints_route_sequence"),
        CheckConstraint("sequence >= 0", name="ck_waypoints_sequence"),
        CheckConstraint("latitude BETWEEN -90 AND 90", name="ck_waypoints_latitude"),
        CheckConstraint("longitude BETWEEN -180 AND 180", name="ck_waypoints_longitude"),
    )

    id: Mapped[UUID] = uuid_pk()
    route_id: Mapped[UUID] = mapped_column(
        ForeignKey("routes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    arrival_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    departure_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    route: Mapped["Route"] = relationship(back_populates="waypoints")
