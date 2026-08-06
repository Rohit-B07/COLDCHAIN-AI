"""Primary health centre request/response DTOs."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domain.entities.facility import MAX_CAPACITY, MIN_CAPACITY


class PhcCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    code: str = Field(min_length=2, max_length=32)
    district: str = Field(min_length=1, max_length=128)
    state: str = Field(min_length=1, max_length=128)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    contact: str = Field(default="", max_length=64)
    capacity: int = Field(default=MIN_CAPACITY, ge=MIN_CAPACITY, le=MAX_CAPACITY)
    priority_level: int = Field(default=1, ge=1, le=10)

    @field_validator("code", mode="before")
    @classmethod
    def normalize_code(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip().upper()
        return value


class PhcUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    code: str | None = Field(default=None, min_length=2, max_length=32)
    district: str | None = Field(default=None, min_length=1, max_length=128)
    state: str | None = Field(default=None, min_length=1, max_length=128)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    contact: str | None = Field(default=None, max_length=64)
    capacity: int | None = Field(default=None, ge=MIN_CAPACITY, le=MAX_CAPACITY)
    priority_level: int | None = Field(default=None, ge=1, le=10)

    @field_validator("code", mode="before")
    @classmethod
    def normalize_code(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip().upper()
        return value


class PhcRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    code: str
    district: str
    state: str
    latitude: float
    longitude: float
    contact: str
    capacity: int
    priority_level: int
    is_deleted: bool = False
    created_at: datetime | None = None


class PhcQueryParams(BaseModel):
    """Query params for listing and filtering primary health centres."""

    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)
    search: str | None = Field(default=None, max_length=100)
    state: str | None = Field(default=None, max_length=128)
    capacity_min: int | None = Field(default=None, ge=0, le=MAX_CAPACITY)
    capacity_max: int | None = Field(default=None, ge=0, le=MAX_CAPACITY)
    priority_level: int | None = Field(default=None, ge=1, le=10)
