"""Async database infrastructure.

Centralises everything persistence-related: the async engine, session factory,
declarative base, connection pooling, health-check helper and startup
initialisation. Feature code depends on the `get_db` dependency / `Base` and
never constructs engines itself.
"""

from app.core.database.base import Base
from app.core.database.engine import engine
from app.core.database.health import database_unhealthy, is_database_healthy
from app.core.database.init import init_db, initialize_database
from app.core.database.session import async_session_factory, get_db, session_scope

__all__ = [
    "Base",
    "async_session_factory",
    "database_unhealthy",
    "engine",
    "get_db",
    "init_db",
    "initialize_database",
    "is_database_healthy",
    "session_scope",
]