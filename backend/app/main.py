"""FastAPI application factory.

Composes the application: middleware, exception handlers, CORS, router
registration, and lifespan lifecycle. Kept deliberately thin so that feature
modules stay self-contained.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.errors import register_exception_handlers
from app.api.middleware.rbac import AuthorizationMiddleware
from app.api.routes import api_router
from app.core.config import get_settings
from app.core.logging import setup_logging

settings = get_settings()
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application startup/shutdown lifecycle.

    Database connection warm-up and resource disposal belong here so tests
    and workers share the same lifecycle semantics.
    """
    yield


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

    application.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.add_middleware(AuthorizationMiddleware)

    application.include_router(api_router, prefix=settings.API_V1_STR)
    register_exception_handlers(application)

    @application.get("/", include_in_schema=False)
    def root() -> dict:
        return {"name": settings.APP_NAME, "version": settings.APP_VERSION}

    return application


app = create_app()
