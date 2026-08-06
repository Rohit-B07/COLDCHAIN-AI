"""Vehicle request/response DTOs."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.entities.logistics import MAX_CAPACITY_KG, MIN_CAPACITY_KG

VehicleTypeValue = Literal[
    "refrigerated_van", "refrigerated_truck", "motorcycle_cooler"
]
VehicleStatusValue = Literal["active", "maintenance", "retired"]
MaintenanceStatusValue = Literal["ok", "scheduled", "in_progress", "overdue"]


class VehicleCreate(BaseModel):
    registration_number: str = Field(min_length=2, max_length=32)
    vehicle_type: VehicleTypeValue = "refrigerated_van"
    capacity_kg: int = Field(default=500, ge=MIN_CAPACITY_KG, le=MAX_CAPACITY_KG)
    is_reefer: bool = True


class VehicleUpdate(BaseModel):
    registration_number: str | None = Field(default=None, min_length=2, max_length=32)
    vehicle_type: VehicleTypeValue | None = None
    capacity_kg: int | None = Field(
        default=None, ge=MIN_CAPACITY_KG, le=MAX_CAPACITY_KG
    )
    is_reefer: bool | None = None


class VehicleStatusUpdate(BaseModel):
    status: VehicleStatusValue


class VehicleMaintenanceUpdate(BaseModel):
    maintenance_status: MaintenanceStatusValue
    last_maintenance_at: datetime | None = None
    next_maintenance_due_at: datetime | None = None


class VehicleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    registration_number: str
    vehicle_type: str
    capacity_kg: int
    is_reefer: bool
    status: str
    maintenance_status: str
    last_maintenance_at: datetime | None = None
    next_maintenance_due_at: datetime | None = None
    is_deleted: bool = False
    created_at: datetime | None = None


class VehicleQueryParams(BaseModel):
    """Query params for listing and filtering vehicles."""

    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)
    search: str | None = Field(default=None, max_length=100)
    status: VehicleStatusValue | None = None
    vehicle_type: VehicleTypeValue | None = None
