"""Unit tests for the weather service (no DB or real network).

Uses an in-memory repository and a stubbed httpx client so the cache-first
flow, provider parsing, retry/fallback behaviour, and background refresh are
all exercised deterministically.
"""

from datetime import UTC, datetime, timedelta

import httpx

from app.core.config import Settings
from app.domain.entities.intelligence import WeatherSnapshot
from app.domain.repositories import WeatherCacheRepository
from app.services.weather_service import WeatherProviderError, WeatherService


class FakeWeatherRepository(WeatherCacheRepository):
    """In-memory stand-in for the weather cache port."""

    def __init__(self) -> None:
        self._store: dict[tuple[float, float], WeatherSnapshot] = {}

    async def get(self, latitude: float, longitude: float) -> WeatherSnapshot | None:
        snapshot = self._store.get((latitude, longitude))
        if (
            snapshot is not None
            and snapshot.expires_at
            and snapshot.expires_at < datetime.now(UTC)
        ):
            return None
        return snapshot

    async def upsert(self, snapshot: WeatherSnapshot) -> None:
        self._store[(snapshot.latitude, snapshot.longitude)] = snapshot

    async def list_cached(self) -> list[WeatherSnapshot]:
        return list(self._store.values())

    async def delete(self, latitude: float, longitude: float) -> None:
        self._store.pop((latitude, longitude), None)


class StubTransport(httpx.AsyncBaseTransport):
    """Returns a canned OpenWeather payload without network I/O."""

    def __init__(self, payload: dict, status_code: int = 200) -> None:
        self._payload = payload
        self._status_code = status_code

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            self._status_code,
            json=self._payload,
            request=request,
        )


def _settings(**overrides: object) -> Settings:
    base = {
        "WEATHER_API_KEY": "test-key",
        "WEATHER_RETRY_ATTEMPTS": 2,
        "WEATHER_RETRY_BACKOFF_SECONDS": 0.01,
        "WEATHER_CACHE_TTL_MINUTES": 30,
    }
    base.update(overrides)
    return Settings(**base)


def _payload() -> dict:
    return {
        "main": {"temp": 21.5, "humidity": 55},
        "weather": [{"main": "Clouds", "description": "broken clouds"}],
        "wind": {"speed": 4.0},
        "clouds": {"all": 75},
        "visibility": 10000,
        "rain": {"1h": 1.2},
    }


class TestGetWeather:
    async def test_serves_fresh_cache_without_calling_provider(self) -> None:
        repo = FakeWeatherRepository()
        snapshot = WeatherSnapshot(
            latitude=18.9,
            longitude=72.8,
            temperature_c=20.0,
            condition="sunny",
            humidity_pct=50.0,
            wind_kmh=5.0,
            precipitation_mm=0.0,
            is_mock=False,
            source="openweather",
            fetched_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(minutes=30),
        )
        await repo.upsert(snapshot)
        service = WeatherService(repo, settings=_settings())
        result = await service.get_weather(18.9, 72.8)
        assert result is snapshot

    async def test_fetches_and_caches_from_provider(self) -> None:
        repo = FakeWeatherRepository()
        client = httpx.AsyncClient(transport=StubTransport(_payload()))
        service = WeatherService(repo, settings=_settings(), client=client)
        result = await service.get_weather(18.9, 72.8)
        assert result.is_mock is False
        assert result.source == "openweather"
        assert result.temperature_c == 21.5
        assert result.humidity_pct == 55.0
        assert result.wind_kmh == round(4.0 * 3.6, 1)
        assert result.precipitation_mm == 1.2
        assert result.condition == "clouds"
        assert result.forecast["clouds_pct"] == 75
        assert await repo.get(18.9, 72.8) is result

    async def test_falls_back_to_mock_when_provider_fails(self) -> None:
        repo = FakeWeatherRepository()
        client = httpx.AsyncClient(transport=StubTransport({}, status_code=500))
        service = WeatherService(repo, settings=_settings(), client=client)
        result = await service.get_weather(18.9, 72.8)
        assert result.is_mock is True
        assert result.source == "mock"
        assert result.temperature_c == round(
            16.0 + ((abs(18900 + 72800) % 240) / 10.0), 1
        )

    async def test_mock_mode_without_api_key(self) -> None:
        repo = FakeWeatherRepository()
        service = WeatherService(repo, settings=_settings(WEATHER_API_KEY=""))
        result = await service.get_weather(18.9, 72.8)
        assert result.is_mock is True
        assert result.source == "mock"


class TestRefreshCached:
    async def test_refreshes_expiring_entries_only(self) -> None:
        repo = FakeWeatherRepository()
        stale = WeatherSnapshot(
            latitude=1.0,
            longitude=2.0,
            temperature_c=10.0,
            condition="sunny",
            humidity_pct=40.0,
            wind_kmh=5.0,
            precipitation_mm=0.0,
            is_mock=False,
            source="openweather",
            fetched_at=datetime.now(UTC) - timedelta(hours=1),
            expires_at=datetime.now(UTC) - timedelta(minutes=1),
        )
        fresh = WeatherSnapshot(
            latitude=3.0,
            longitude=4.0,
            temperature_c=15.0,
            condition="rainy",
            humidity_pct=60.0,
            wind_kmh=8.0,
            precipitation_mm=2.0,
            is_mock=False,
            source="openweather",
            fetched_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(minutes=120),
        )
        await repo.upsert(stale)
        await repo.upsert(fresh)
        client = httpx.AsyncClient(transport=StubTransport(_payload()))
        service = WeatherService(repo, settings=_settings(), client=client)
        refreshed = await service.refresh_cached()
        assert refreshed == 1
        updated = await repo.get(1.0, 2.0)
        assert updated is not None
        assert updated.temperature_c == 21.5
        assert updated.expires_at and updated.expires_at > datetime.now(UTC)

    async def test_returns_zero_when_api_key_missing(self) -> None:
        repo = FakeWeatherRepository()
        service = WeatherService(repo, settings=_settings(WEATHER_API_KEY=""))
        assert await service.refresh_cached() == 0


class TestRetry:
    async def test_retries_then_raises_after_exhaustion(self) -> None:
        class AlwaysFail(httpx.AsyncBaseTransport):
            async def handle_async_request(
                self, request: httpx.Request
            ) -> httpx.Response:
                raise httpx.ConnectError("boom", request=request)

        service = WeatherService(
            FakeWeatherRepository(),
            settings=_settings(),
            client=httpx.AsyncClient(transport=AlwaysFail()),
        )
        try:
            await service._fetch_with_retry(0.0, 0.0)
        except WeatherProviderError as exc:
            assert "after 2 attempts" in str(exc)
        else:
            raise AssertionError("expected WeatherProviderError")
