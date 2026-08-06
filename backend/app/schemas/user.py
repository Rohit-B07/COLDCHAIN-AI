"""User management request/response DTOs."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.domain.value_objects import UserRole


class UserProfileRead(BaseModel):
    """Full profile returned for the current user."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime | None = None


class UserSummaryRead(UserProfileRead):
    """Concise user row used in listing responses."""


class UserUpdateProfile(BaseModel):
    """Profile edit payload; only provided fields are updated."""

    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    email: EmailStr | None = None


class ChangePasswordRequest(BaseModel):
    """Password change payload requiring the current password."""

    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


class UserQueryParams(BaseModel):
    """Query params for listing and filtering users."""

    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)
    search: str | None = Field(default=None, max_length=100)
    role: UserRole | None = None
    is_active: bool | None = None
