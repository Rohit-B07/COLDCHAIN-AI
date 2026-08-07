"""Weather service: OpenWeather provider with caching and graceful fallback.

The service is the application boundary for weather data. It implements the
cache-then-provider flow, retries with exponential backoff against the
OpenWeather API, and degrades to a deterministic mock when no API key is
configured or the provider is unreachable. All I/O happens over ``httpx`` so
the rest of the application stays provider-agnostic.
"""

import asyncio
import logging
from datetime import UTC, datetime, timedelta

import httpx

from app.core.config import Settings, get_settings
from app.domain.entities.intelligence import WeatherSnapshot
from app.domain.repositories import WeatherCacheRepository

logger = logging.getLogger("coldchain_api.weather")


class WeatherProviderError(Exception):
    """Raised when the weather provider cannot be reached after retries."""


class WeatherService:
    """Fetches, caches and refreshes weather snapshots for coordinates."""

    def __init__(
        self,
        weather_repo: WeatherCacheRepository,
        *,
        settings: Settings | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._repo = weather_repo
        self._settings = settings or get_settings()
        self._client = client or httpx.AsyncClient(
            timeout=httpx.Timeout(self._settings.WEATHER_HTTP_TIMEOUT_SECONDS)
        )

    # ---- Public API -----------------------------------------------------------

    async def get_weather(self, latitude: float, longitude: float) -> WeatherSnapshot:
        """Return cached weather or fetch, cache and return a fresh snapshot."""
        cached = await self._repo.get(latitude, longitude)
        if cached is not None and not self._should_refresh(cached):
            return cached
        try:
            snapshot = await self._fetch_with_retry(latitude, longitude)
        except WeatherProviderError:
            logger.warning(
                "Weather provider unavailable for (%.4f, %.4f); using mock fallback",
                latitude,
                longitude,
            )
            snapshot = self._mock(latitude, longitude)
        await self._repo.upsert(snapshot)
        return snapshot

    async def refresh_cached(self, *, stale_within_minutes: int | None = None) -> int:
        """Refresh cached entries whose TTL is about to expire.

        Returns the number of entries refreshed. Called by the lifespan
        background task on an interval so commonly requested coordinates stay
        warm without waiting for a cold cache miss.
        """
        if (
            self._settings.WEATHER_API_KEY is None
            or self._settings.WEATHER_API_KEY == ""
        ):
            return 0
        window = stale_within_minutes or self._settings.WEATHER_CACHE_TTL_MINUTES
        horizon = datetime.now(UTC) + timedelta(minutes=window)
        refreshed = 0
        for cached in await self._repo.list_cached():
            if cached.expires_at is not None and cached.expires_at > horizon:
                continue
            try:
                snapshot = await self._fetch_with_retry(
                    cached.latitude, cached.longitude
                )
            except WeatherProviderError:
                logger.warning(
                    "Background refresh failed for (%.4f, %.4f)",
                    cached.latitude,
                    cached.longitude,
                )
                continue
            await self._repo.upsert(snapshot)
            refreshed += 1
        return refreshed

    # ---- Provider ---------------------------------------------------------------

    async def _fetch_with_retry(
        self, latitude: float, longitude: float
    ) -> WeatherSnapshot:
        if (
            self._settings.WEATHER_API_KEY is None
            or self._settings.WEATHER_API_KEY == ""
        ):
            return self._mock(latitude, longitude)
        attempts = max(1, self._settings.WEATHER_RETRY_ATTEMPTS)
        last_error: Exception | None = None
        for attempt in range(1, attempts + 1):
            try:
                return await self._fetch(latitude, longitude)
            except (httpx.HTTPError, httpx.TimeoutException) as exc:
                last_error = exc
                if attempt < attempts:
                    delay = self._settings.WEATHER_RETRY_BACKOFF_SECONDS * (
                        2 ** (attempt - 1)
                    )
                    await asyncio.sleep(delay)
        raise WeatherProviderError(
            f"OpenWeather unreachable after {attempts} attempts"
        ) from last_error

    async def _fetch(self, latitude: float, longitude: float) -> WeatherSnapshot:
        params = {
            "lat": latitude,
            "lon": longitude,
            "appid": self._settings.WEATHER_API_KEY,
            "units": self._settings.WEATHER_UNITS,
        }
        response = await self._client.get(
            f"{self._settings.WEATHER_API_URL}/weather", params=params
        )
        response.raise_for_status()
        payload = response.json()
        now = datetime.now(UTC)
        return WeatherSnapshot(
            latitude=latitude,
            longitude=longitude,
            temperature_c=round(payload["main"]["temp"], 1),
            condition=payload["weather"][0]["main"].lower(),
            humidity_pct=round(payload["main"]["humidity"], 1),
            wind_kmh=round(payload["wind"]["speed"] * 3.6, 1),
            precipitation_mm=self._precipitation_mm(payload),
            is_mock=False,
            source="openweather",
            forecast={
                "visibility_m": payload.get("visibility"),
                "pressure_hpa": payload.get("main", {}).get("pressure"),
                "clouds_pct": payload.get("clouds", {}).get("all"),
                "description": payload.get("weather", [{}])[0].get("description"),
            },
            fetched_at=now,
            expires_at=now
            + timedelta(minutes=self._settings.WEATHER_CACHE_TTL_MINUTES),
        )

    # ---- Helpers -----------------------------------------------------------------

    @staticmethod
    def _precipitation_mm(payload: dict) -> float:
        rain = payload.get("rain", {})
        if isinstance(rain, dict) and "1h" in rain:
            return round(float(rain["1h"]), 1)
        snow = payload.get("snow", {})
        if isinstance(snow, dict) and "1h" in snow:
            return round(float(snow["1h"]), 1)
        return 0.0

    @staticmethod
    def _should_refresh(snapshot: WeatherSnapshot) -> bool:
        if snapshot.expires_at is None:
            return False
        return snapshot.expires_at < datetime.now(UTC)

    @staticmethod
    def _mock(latitude: float, longitude: float) -> WeatherSnapshot:
        """Deterministic mock forecast so the module runs offline."""
        seed = abs(int(latitude * 1000) + int(longitude * 1000))
        temp = 16.0 + (seed % 240) / 10.0
        humidity = 40.0 + (seed % 45)
        wind = 5.0 + (seed % 25)
        precip = 0.0 if seed % 3 == 0 else 2.0
        condition = "sunny" if precip == 0.0 else "rainy"
        now = datetime.now(UTC)
        return WeatherSnapshot(
            latitude=latitude,
            longitude=longitude,
            temperature_c=round(temp, 1),
            condition=condition,
            humidity_pct=round(humidity, 1),
            wind_kmh=round(wind, 1),
            precipitation_mm=round(precip, 1),
            is_mock=True,
            source="mock",
            fetched_at=now,
            expires_at=now + timedelta(minutes=30),
        )

    async def aclose(self) -> None:
        """Release the underlying HTTP client."""
        await self._client.aclose()
