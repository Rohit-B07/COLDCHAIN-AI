"""Shipment DTOs."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.value_objects import Priority, ShipmentStatus


class ShipmentCreate(BaseModel):
    vaccine_name: str = Field(min_length=1, max_length=255)
    dose_count: int = Field(ge=0)
    warehouse_id: UUID
    destination_id: UUID
    priority: Priority = Priority.MEDIUM
    temperature_min: float = Field(default=2.0)
    temperature_max: float = Field(default=8.0)
    container_id: UUID | None = None
    driver_id: UUID | None = None


class ShipmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tracking_code: str
    vaccine_name: str
    dose_count: int
    priority: Priority
    temperature_min: float
    temperature_max: float
    warehouse_id: UUID
    destination_id: UUID
    container_id: UUID | None
    driver_id: UUID | None
    status: ShipmentStatus
    dispatched_at: datetime | None
    delivered_at: datetime | None
    estimated_delivery_at: datetime | None
    created_at: datetime


class DispatchRequest(BaseModel):
    container_id: UUID
    driver_id: UUID


class AlertsOutcome(BaseModel):
    alerts: list[str] = Field(default_factory=list)