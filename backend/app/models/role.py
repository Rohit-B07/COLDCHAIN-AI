"""Role model and user-role association table.

Roles drive role-based access control. A user may hold several roles via the
many-to-many ``user_roles`` link table. Roles support soft deletion so audit
trails (historical user-role associations) survive removal.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, Column, ForeignKey, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import TimestampMixin, uuid_pk

if TYPE_CHECKING:
    from app.models.user import User

user_roles = Table(
    "user_roles",
    Base.metadata,
    Column(
        "user_id",
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "role_id",
        ForeignKey("roles.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Role(TimestampMixin, Base):
    """A discrete access-control role assignable to users."""

    __tablename__ = "roles"

    id: Mapped[UUID] = uuid_pk()
    name: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False
    )
    description: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    is_deleted: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, index=True
    )

    users: Mapped[list[User]] = relationship(  # noqa: F821
        secondary=user_roles, back_populates="roles"
    )
