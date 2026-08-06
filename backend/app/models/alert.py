"""ColdAlert model: excursions, geofence and system alerts."""

import enum
from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.base import TimestampMixin, uuid_pk


class AlertSeverity(str, enum.Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertStatus(str, enum.Enum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class ColdAlert(TimestampMixin, Base):
    __tablename__ = "cold_alerts"

    id: Mapped[UUID] = uuid_pk()
    shipment_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("shipments.id", ondelete="CASCADE"), nullable=True, index=True
    )
    container_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("cold_containers.id", ondelete="CASCADE"), nullable=True, index=True
    )
    severity: Mapped[AlertSeverity] = mapped_column(
        String(16), nullable=False, default=AlertSeverity.INFO.value
    )
    alert_type: Mapped[str] = mapped_column(String(64), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[AlertStatus] = mapped_column(
        String(24), nullable=False, default=AlertStatus.OPEN.value
    )
    acknowledged_by: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    acknowledged_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
