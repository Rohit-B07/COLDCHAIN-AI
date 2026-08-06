"""Logistics asset DTOs."""

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

VehicleTypeLiteral = Literal["refrigerated_van", "refrigerated_truck", "motorcycle_cooler"]


class DriverCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    phone: str = Field(min_length=10, max_length=15, pattern=r"^\+?[0-9]{10,15}$")
    license_number: str = Field(min_length=1, max_length=64)
    vehicle_id: UUID | None = None


class DriverRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    phone: str
    license_number: str
    status: str
    vehicle_id: UUID | None


class VehicleCreate(BaseModel):
    registration_number: str = Field(min_length=1, max_length=32)
    vehicle_type: VehicleTypeLiteral = "refrigerated_van"
    capacity_kg: int = Field(default=500, ge=0, le=100_000)
    is_reefer: bool = True

    @field_validator("registration_number")
    @classmethod
    def normalize_registration(cls, value: str) -> str:
        return value.strip().upper()


class VehicleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    registration_number: str
    vehicle_type: str
    capacity_kg: int
    is_reefer: bool
    status: str


class ContainerCreate(BaseModel):
    asset_tag: str = Field(min_length=1, max_length=64)
    temperature_setpoint: float = Field(default=4.0)
    min_temperature: float = Field(default=2.0)
    max_temperature: float = Field(default=8.0)


class ContainerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    asset_tag: str
    temperature_setpoint: float
    min_temperature: float
    max_temperature: float
    status: str
    current_latitude: float | None
    current_longitude: float | None
    battery_level: int


class ContainerLocationUpdate(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    battery_level: int = Field(ge=0, le=100)
