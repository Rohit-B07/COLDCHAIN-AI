"""FastAPI application factory.

Composes the application: middleware, exception handlers, CORS, router
registration, and lifespan lifecycle. Kept deliberately thin so that feature
modules stay self-contained.
"""

import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.errors import register_exception_handlers
from app.api.middleware.rbac import AuthorizationMiddleware
from app.api.routes import api_router
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.db.session import async_session_factory
from app.repositories.weather import SqlAlchemyWeatherCacheRepository
from app.services.weather_service import WeatherService

settings = get_settings()
setup_logging()

logger = logging.getLogger("coldchain_api.main")


async def _weather_refresh_loop() -> None:
    """Periodically refresh soon-to-expire cached weather entries.

    Runs for the application's lifetime; the lifespan cancels it on shutdown.
    Refreshing in the background keeps commonly requested coordinates warm so
    live requests hit the cache instead of paying an API round-trip.
    """
    interval_minutes = settings.WEATHER_BACKGROUND_REFRESH_INTERVAL_MINUTES
    if interval_minutes <= 0:
        return
    while True:
        try:
            async with async_session_factory() as session:
                service = WeatherService(
                    weather_repo=SqlAlchemyWeatherCacheRepository(session),
                    settings=settings,
                )
                refreshed = await service.refresh_cached()
                if refreshed:
                    logger.info("Background weather refresh updated %d entries", refreshed)
                await service.aclose()
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Background weather refresh failed")
        await asyncio.sleep(interval_minutes * 60)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application startup/shutdown lifecycle.

    Database connection warm-up and resource disposal belong here so tests
    and workers share the same lifecycle semantics.
    """
    task = asyncio.create_task(_weather_refresh_loop())
    yield
    task.cancel()
    with suppress(asyncio.CancelledError):
        await task


def create_app() -> FastAPI:
    """Build and configure the FastAPI application instance."""
    application = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "ColdChain AI - AI-powered decision support for vaccine cold-chain "
            "delivery: temperature-excursion prediction and safe route planning."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        lifespan=lifespan,
    )

    application.add_middleware(AuthorizationMiddleware)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(api_router, prefix=settings.API_V1_STR)
    register_exception_handlers(application)

    @application.get("/", include_in_schema=False)
    def root() -> dict:
        return {"name": settings.APP_NAME, "version": settings.APP_VERSION}

    return application


app = create_app()
