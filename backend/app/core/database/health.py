"""Database health-check helpers.

These are pure infrastructure helpers: they probe connectivity through the
shared engine. Liveness/readiness exposure belongs to the API layer, which
calls these functions.
"""

import logging

from sqlalchemy import text

from app.core.database.engine import engine

logger = logging.getLogger("coldchain_api.database.health")


async def is_database_healthy() -> bool:
    """Return True when the database answers a trivial query."""
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        return True
    except Exception:
        logger.exception("Database health probe failed")
        return False


async def database_unhealthy() -> None:
    """Raise on failure so callers can react with structured logging."""
    if not await is_database_healthy():
        raise RuntimeError("database is unreachable")
