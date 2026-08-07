"""Async engine construction with production-ready connection pooling.

The engine is created once at import time and shared across the process. Pool
behaviour is fully environment-driven so operators can tune concurrency without
touching code.
"""

import asyncio
import sys

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from app.core.config import get_settings

settings = get_settings()

engine: AsyncEngine = create_async_engine(
    settings.sqlalchemy_database_url,
    pool_pre_ping=settings.DATABASE_POOL_PRE_PING,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_timeout=settings.DATABASE_POOL_TIMEOUT,
    pool_recycle=settings.DATABASE_POOL_RECYCLE,
    echo=settings.DEBUG,
    connect_args={"connect_timeout": settings.DB_CONNECT_TIMEOUT},
    future=True,
)
