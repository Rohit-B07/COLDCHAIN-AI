"""Declarative base for SQLAlchemy ORM models.

Import any model module that must be registered with the metadata before
running Alembic autogenerate or `Base.metadata.create_all`.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all ORM models.

    Every model in `app/models` should inherit from this class so that its
    table is discovered by Alembic autogeneration.
    """

    pass


# Import models here so they register with `Base.metadata`.
# from app.models.shipment import Shipment  # noqa: E402,F401
