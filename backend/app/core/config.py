"""Application configuration.

Centralised, environment-driven configuration using Pydantic Settings.
Every environment variable that the backend consumes is declared here so that
configuration remains typed, validated, and documented in a single location.
"""

from functools import lru_cache
from typing import Literal

from pydantic import (
    AnyHttpUrl,
    PostgresDsn,
    ValidationInfo,
    field_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed application settings, populated from environment variables.

    A `.env` file at the repository root (or under `backend/`) is loaded
    automatically for local development. In production, values are injected
    by the container runtime.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---- Application ----------------------------------------------------------
    APP_NAME: str = "ColdChain AI API"
    APP_VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False
    ENVIRONMENT: Literal["development", "testing", "production"] = "development"

    # ---- CORS -----------------------------------------------------------------
    BACKEND_CORS_ORIGINS: list[AnyHttpUrl] = []

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, value: str | list[str]) -> list[str] | str:
        """Allow CORS origins to be supplied as a comma separated string."""
        if isinstance(value, str) and not value.startswith("["):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        if isinstance(value, str | list):
            return value
        raise ValueError(value)

    # ---- Security (dev defaults follow; override via environment) -------------
    SECRET_KEY: str = "change-me-in-production"  # noqa: S105
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    JWT_ISSUER: str = "coldchain-ai"

    # ---- Database -------------------------------------------------------------
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "coldchain"
    POSTGRES_PASSWORD: str = "coldchain"  # noqa: S105
    POSTGRES_DB: str = "coldchain"
    DATABASE_URL: PostgresDsn | None = None
    DB_CONNECT_TIMEOUT: int = 5  # seconds; fail fast instead of hanging

    # ---- Database connection pool --------------------------------------------
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_POOL_RECYCLE: int = 1800  # seconds; recycle connections before PG timeout
    DATABASE_POOL_PRE_PING: bool = True
    DATABASE_INITIALIZE_ON_STARTUP: bool = False

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_database_url(
        cls, value: str | None, info: ValidationInfo
    ) -> str | None:
        """Build a Postgres DSN from parts when not supplied directly."""
        if isinstance(value, str) and value:
            return value
        host = info.data.get("POSTGRES_HOST", "localhost")
        port = info.data.get("POSTGRES_PORT", 5432)
        user = info.data.get("POSTGRES_USER", "coldchain")
        password = info.data.get("POSTGRES_PASSWORD", "coldchain")
        db = info.data.get("POSTGRES_DB", "coldchain")
        return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{db}"

    # ---- Logging --------------------------------------------------------------
    LOG_LEVEL: str = "INFO"

    # ---- Initial admin / database seeding ------------------------------------
    # Credentials for the bootstrap admin user, injected by environment in
    # production. Only applied when the seed script runs.
    SEED_ADMIN_EMAIL: str = "admin@coldchain.local"
    SEED_ADMIN_PASSWORD: str = "ChangeMe!123"  # noqa: S105
    SEED_ADMIN_FULL_NAME: str = "ColdChain Administrator"

    # ---- Feature toggles (no business logic yet, but wiring for later) --------
    ENABLE_TELEMETRY: bool = False

    @property
    def sqlalchemy_database_url(self) -> str:
        """Return the DSN as a plain string for SQLAlchemy."""
        return str(self.DATABASE_URL)


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance.

    Caching avoids re-parsing environment variables and re-running validators
    on every request. In tests, this cache is cleared and overridden.
    """
    return Settings()
