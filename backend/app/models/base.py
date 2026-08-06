"""Shared SQLAlchemy helpers for ORM models."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID as SAUUID
from sqlalchemy.orm import Mapped, mapped_column


class TimestampMixin:
    """Adds created_at/updated_at columns to a model."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


def uuid_pk() -> Mapped[UUID]:
    """Return a mapped column used as the standard primary key."""
    return mapped_column(
        SAUUID(as_uuid=True), primary_key=True, default=uuid4, nullable=False
    )  # type: ignore[return-value]
