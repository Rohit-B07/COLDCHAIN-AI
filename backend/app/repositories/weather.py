"""SQLAlchemy async repository for the weather cache."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.intelligence import WeatherSnapshot
from app.models.weather import WeatherCache as WeatherCacheModel
from app.repositories.base import to_weather_entity


class SqlAlchemyWeatherCacheRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, latitude: float, longitude: float) -> WeatherSnapshot | None:
        result = await self._session.execute(
            select(WeatherCacheModel)
            .where(
                WeatherCacheModel.latitude == latitude,
                WeatherCacheModel.longitude == longitude,
            )
            .limit(1)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        if model.expires_at < datetime.now(UTC):
            return None
        return to_weather_entity(model)

    async def upsert(self, snapshot: WeatherSnapshot) -> None:
        now = datetime.now(UTC)
        ttl = timedelta(hours=1)
        expires_at = snapshot.expires_at or now + ttl
        result = await self._session.execute(
            select(WeatherCacheModel)
            .where(
                WeatherCacheModel.latitude == snapshot.latitude,
                WeatherCacheModel.longitude == snapshot.longitude,
            )
            .limit(1)
        )
        model = result.scalar_one_or_none()
        if model is None:
            self._session.add(
                WeatherCacheModel(
                    latitude=snapshot.latitude,
                    longitude=snapshot.longitude,
                    temperature_c=snapshot.temperature_c,
                    precipitation_mm=snapshot.precipitation_mm,
                    wind_kmh=snapshot.wind_kmh,
                    humidity_pct=snapshot.humidity_pct,
                    condition=snapshot.condition,
                    source=snapshot.source or "mock",
                    forecast=snapshot.forecast or {},
                    is_mock=snapshot.is_mock,
                    fetched_at=snapshot.fetched_at or now,
                    expires_at=expires_at,
                )
            )
        else:
            model.temperature_c = snapshot.temperature_c
            model.precipitation_mm = snapshot.precipitation_mm
            model.wind_kmh = snapshot.wind_kmh
            model.humidity_pct = snapshot.humidity_pct
            model.condition = snapshot.condition
            model.source = snapshot.source or "mock"
            model.forecast = snapshot.forecast or {}
            model.is_mock = snapshot.is_mock
            model.fetched_at = snapshot.fetched_at or now
            model.expires_at = expires_at
        await self._session.flush()

    async def list_cached(self) -> list[WeatherSnapshot]:
        result = await self._session.execute(select(WeatherCacheModel))
        return [to_weather_entity(model) for model in result.scalars().all()]

    async def delete(self, latitude: float, longitude: float) -> None:
        await self._session.execute(
            delete(WeatherCacheModel).where(
                WeatherCacheModel.latitude == latitude,
                WeatherCacheModel.longitude == longitude,
            )
        )
        await self._session.flush()
