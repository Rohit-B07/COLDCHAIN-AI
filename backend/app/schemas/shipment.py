"""Shipment DTOs."""

import enum
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.domain.entities.shipment import (
    MAX_DOSE_COUNT,
    MAX_TEMPERATURE,
    MIN_DOSE_COUNT,
    MIN_TEMPERATURE,
)
from app.domain.value_objects import Priority, ShipmentStatus


class ShipmentCreate(BaseModel):
    vaccine_name: str = Field(min_length=1, max_length=255)
    dose_count: int = Field(ge=MIN_DOSE_COUNT, le=MAX_DOSE_COUNT)
    warehouse_id: UUID
    destination_id: UUID
    priority: Priority = Priority.MEDIUM
    temperature_min: float = Field(default=2.0, ge=MIN_TEMPERATURE, le=MAX_TEMPERATURE)
    temperature_max: float = Field(default=8.0, ge=MIN_TEMPERATURE, le=MAX_TEMPERATURE)
    container_id: UUID | None = None
    driver_id: UUID | None = None

    @model_validator(mode="after")
    def _temperature_range(self) -> "ShipmentCreate":
        if self.temperature_min >= self.temperature_max:
            raise ValueError("temperature_min must be less than temperature_max")
        return self


class ShipmentUpdate(BaseModel):
    vaccine_name: str | None = Field(default=None, min_length=1, max_length=255)
    dose_count: int | None = Field(default=None, ge=MIN_DOSE_COUNT, le=MAX_DOSE_COUNT)
    priority: Priority | None = None
    temperature_min: float | None = Field(
        default=None, ge=MIN_TEMPERATURE, le=MAX_TEMPERATURE
    )
    temperature_max: float | None = Field(
        default=None, ge=MIN_TEMPERATURE, le=MAX_TEMPERATURE
    )
    container_id: UUID | None = None
    driver_id: UUID | None = None
    estimated_delivery_at: datetime | None = None

    @model_validator(mode="after")
    def _temperature_range(self) -> "ShipmentUpdate":
        if (
            self.temperature_min is not None
            and self.temperature_max is not None
            and self.temperature_min >= self.temperature_max
        ):
            raise ValueError("temperature_min must be less than temperature_max")
        return self


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
    is_deleted: bool = False
    deleted_at: datetime | None = None


class ShipmentSortField(str, enum.Enum):
    CREATED_AT = "created_at"
    TRACKING_CODE = "tracking_code"
    STATUS = "status"
    PRIORITY = "priority"
    VACCINE_NAME = "vaccine_name"
    ESTIMATED_DELIVERY_AT = "estimated_delivery_at"


class ShipmentSortOrder(str, enum.Enum):
    ASC = "asc"
    DESC = "desc"


class ShipmentQueryParams(BaseModel):
    """Query params for listing and filtering shipments."""

    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)
    search: str | None = Field(default=None, max_length=100)
    shipment_id: UUID | None = None
    tracking_code: str | None = Field(default=None, max_length=64)
    origin: UUID | None = None
    destination: UUID | None = None
    status: ShipmentStatus | None = None
    priority: Priority | None = None
    vaccine_type: str | None = Field(default=None, max_length=255)
    created_after: datetime | None = None
    created_before: datetime | None = None
    expected_delivery_after: datetime | None = None
    expected_delivery_before: datetime | None = None
    sort_by: ShipmentSortField = ShipmentSortField.CREATED_AT
    sort_order: ShipmentSortOrder = ShipmentSortOrder.DESC

    @model_validator(mode="after")
    def _validate_date_ranges(self) -> "ShipmentQueryParams":
        if (
            self.created_after is not None
            and self.created_before is not None
            and self.created_after > self.created_before
        ):
            raise ValueError("created_after must be before created_before")
        if (
            self.expected_delivery_after is not None
            and self.expected_delivery_before is not None
            and self.expected_delivery_after > self.expected_delivery_before
        ):
            raise ValueError(
                "expected_delivery_after must be before expected_delivery_before"
            )
        return self


class DispatchRequest(BaseModel):
    container_id: UUID
    driver_id: UUID


class AlertsOutcome(BaseModel):
    alerts: list[str] = Field(default_factory=list)
