"""Role request/response DTOs."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RoleCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50, pattern=r"^[a-z0-9_]+$")
    description: str = Field(default="", max_length=255)

    @field_validator("name", mode="before")
    @classmethod
    def normalize_name(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip().lower()
        return value


class RoleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=50, pattern=r"^[a-z0-9_]+$")
    description: str | None = Field(default=None, max_length=255)


class RoleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
