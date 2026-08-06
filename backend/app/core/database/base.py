"""The single SQLAlchemy declarative Base for the entire project.

Every ORM model inherits from this base, defined once in ``app.db.base``.
This module re-exports that same class so infrastructure code, startup
initialisation and Alembic resolve one and the same registry and metadata.

There is intentionally no ``DeclarativeBase`` subclass defined here — the
codebase must contain exactly one declarative base.
"""

from app.db.base import Base

__all__ = ["Base"]
