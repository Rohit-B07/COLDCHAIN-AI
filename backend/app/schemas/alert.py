"""Alert DTOs: create, update, read and query filters."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

AlertSeverityValue = Literal["info", "warning", "critical"]
AlertStatusValue = Literal["open", "acknowledged", "resolved"]


class AlertCreate(BaseModel):
    severity: AlertSeverityValue = "warning"
    alert_type: str = Field(min_length=1, max_length=64)
    message: str = Field(min_length=1)
    shipment_id: UUID | None = None
    container_id: UUID | None = None


class AlertUpdate(BaseModel):
    severity: AlertSeverityValue | None = None
    alert_type: str | None = Field(default=None, min_length=1, max_length=64)
    message: str | None = Field(default=None, min_length=1)


class AlertRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    shipment_id: UUID | None
    container_id: UUID | None
    severity: AlertSeverityValue
    alert_type: str
    message: str
    status: AlertStatusValue
    acknowledged_by: UUID | None
    acknowledged_at: datetime | None
    created_at: datetime | None


class AlertQueryParams(BaseModel):
    shipment_id: UUID | None = None
    container_id: UUID | None = None
    severity: AlertSeverityValue | None = None
    status: AlertStatusValue | None = None
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)
