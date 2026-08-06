"""Startup database initialisation.

Optional: when ``DATABASE_INITIALIZE_ON_STARTUP`` is true the application
creates missing tables from the ORM metadata at startup. This is convenient for
prototype/CI environments; production deployments rely on Alembic migrations
instead and keep this flag off.
"""

import logging

import app.models  # noqa: F401  (registers every ORM model with Base.metadata)
from app.core.config import get_settings
from app.core.database.base import Base
from app.core.database.engine import engine

logger = logging.getLogger("coldchain_api.database.init")


async def init_db() -> None:
    """Create tables that do not yet exist (idempotent)."""
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    logger.info("Database schema initialised from ORM metadata")


async def initialize_database() -> None:
    """Entry point wired into the application lifespan."""
    settings = get_settings()
    if not settings.DATABASE_INITIALIZE_ON_STARTUP:
        logger.debug("Skipping startup schema initialisation (flag disabled)")
        return
    await init_db()
