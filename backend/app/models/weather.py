"""WeatherCache model: short-lived regional weather snapshots."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import JSON, Boolean, DateTime, Float, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.base import TimestampMixin, uuid_pk


class WeatherCache(TimestampMixin, Base):
    __tablename__ = "weather_cache"
    __table_args__ = (
        UniqueConstraint("latitude", "longitude", name="uq_weather_lat_lon"),
    )

    id: Mapped[UUID] = uuid_pk()
    latitude: Mapped[Decimal] = mapped_column(Float, nullable=False)
    longitude: Mapped[Decimal] = mapped_column(Float, nullable=False)
    temperature_c: Mapped[Decimal] = mapped_column(Float, nullable=False)
    precipitation_mm: Mapped[Decimal] = mapped_column(Float, nullable=False, default=0.0)
    wind_kmh: Mapped[Decimal] = mapped_column(Float, nullable=False, default=0.0)
    humidity_pct: Mapped[Decimal] = mapped_column(Float, nullable=False, default=0.0)
    condition: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    source: Mapped[str] = mapped_column(String(32), nullable=False, default="mock")
    forecast: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    is_mock: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
