"""Database session management (async).

Owns the SQLAlchemy async engine and session factory, providing a FastAPI
dependency (`get_db`) for request-scoped sessions and a module-level
`session_scope` async context manager for scripts and background tasks.

Uses the `psycopg` (v3) driver which supports an `ASYNC` mode natively,
so no extra third-party driver such as asyncpg is required.
"""

from collections.abc import AsyncGenerator, AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.sqlalchemy_database_url,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    echo=settings.DEBUG,
    connect_args={"connect_timeout": settings.DB_CONNECT_TIMEOUT},
)

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding a request-scoped async session.

    Commits the transaction when the request handler completes successfully and
    rolls back on any failure, so write endpoints persist their changes.
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@asynccontextmanager
async def session_scope() -> AsyncIterator[AsyncSession]:
    """Context manager for short-lived sessions outside request handling."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
