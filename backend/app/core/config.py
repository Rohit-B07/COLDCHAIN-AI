"""Application configuration.

Centralised, environment-driven configuration using Pydantic Settings.
Every environment variable that the backend consumes is declared here so that
configuration remains typed, validated, and documented in a single location.
"""

import json
from functools import lru_cache
from typing import Annotated, Literal

from pydantic import (
    PostgresDsn,
    ValidationInfo,
    field_validator,
)
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


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
    # NoDecode prevents pydantic-settings from JSON-decoding the raw value so
    # that the comma-separated string reaches the validator below. Stored as
    # plain strings so origins are kept exactly as configured (AnyHttpUrl would
    # normalise them with a trailing slash, which breaks starlette's exact-match
    # origin comparison in CORSMiddleware).
    BACKEND_CORS_ORIGINS: Annotated[list[str], NoDecode] = []

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, value: str | list[str]) -> list[str]:
        """Allow CORS origins to be supplied as a comma separated string."""
        if isinstance(value, str):
            if value.startswith("["):
                value = json.loads(value)
            else:
                return [
                    origin.strip().rstrip("/")
                    for origin in value.split(",")
                    if origin.strip()
                ]
        if isinstance(value, list):
            return [
                str(origin).strip().rstrip("/")
                for origin in value
                if str(origin).strip()
            ]
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
    SEED_ADMIN_EMAIL: str = "admin@coldchain.io"
    SEED_ADMIN_PASSWORD: str = "ChangeMe!123"  # noqa: S105
    SEED_ADMIN_FULL_NAME: str = "ColdChain Administrator"

    # ---- Feature toggles (no business logic yet, but wiring for later) --------
    ENABLE_TELEMETRY: bool = False

    # ---- Excursion prediction engine ------------------------------------------
    # Rule weights and thresholds for the explainable rule-based model. Each
    # rule contributes a bounded factor; risk = base + weighted rule terms.
    # Confidence is lower when the engine falls back to mock weather.
    PREDICTION_TEMPERATURE_WEIGHT: float = 0.50
    PREDICTION_DURATION_WEIGHT: float = 0.35
    PREDICTION_STOP_WEIGHT: float = 0.15
    PREDICTION_BASE_RISK: float = 0.10
    PREDICTION_PRIORITY_BOOST: float = 0.10
    PREDICTION_MAX_EXPOSURE_DEGREES: float = 20.0
    PREDICTION_MAX_DISTANCE_KM: float = 300.0
    PREDICTION_MAX_STOPS: int = 10
    PREDICTION_DEFAULT_DISTANCE_KM: float = 50.0
    PREDICTION_DEFAULT_STOPS: int = 2
    PREDICTION_CONFIDENCE_LIVE: float = 0.90
    PREDICTION_CONFIDENCE_MOCK: float = 0.60

    # ---- OpenWeather integration ---------------------------------------------
    # Base URL for the OpenWeather API. The "current weather" endpoint is used
    # with a metric (Celsius) unit. Set WEATHER_API_KEY to enable live data; an
    # empty key keeps the service in deterministic mock mode so the module can
    # be developed and demoed offline.
    WEATHER_API_URL: str = "https://api.openweathermap.org/data/2.5"
    WEATHER_API_KEY: str = ""
    WEATHER_UNITS: str = "metric"
    WEATHER_CACHE_TTL_MINUTES: int = 30
    WEATHER_HTTP_TIMEOUT_SECONDS: float = 10.0
    WEATHER_RETRY_ATTEMPTS: int = 3
    WEATHER_RETRY_BACKOFF_SECONDS: float = 1.0
    # How often the lifespan background task refreshes soon-to-expire entries.
    WEATHER_BACKGROUND_REFRESH_INTERVAL_MINUTES: int = 30

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
