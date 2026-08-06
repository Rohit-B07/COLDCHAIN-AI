"""Driver request/response DTOs."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

DriverStatusValue = Literal["available", "assigned", "on_leave"]


class DriverCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    phone: str = Field(min_length=10, max_length=16)
    license_number: str = Field(min_length=6, max_length=32)


class DriverUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    phone: str | None = Field(default=None, min_length=10, max_length=16)
    license_number: str | None = Field(default=None, min_length=6, max_length=32)


class DriverStatusUpdate(BaseModel):
    status: DriverStatusValue


class DriverAssign(BaseModel):
    vehicle_id: UUID


class DriverRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    phone: str
    license_number: str
    status: str
    vehicle_id: UUID | None = None
    is_deleted: bool = False
    created_at: datetime | None = None


class DriverQueryParams(BaseModel):
    """Query params for listing and filtering drivers."""

    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)
    search: str | None = Field(default=None, max_length=100)
    status: DriverStatusValue | None = Field(default=None)
