"""Weather endpoints.

Exposes current weather for a location through the `WeatherService`. The
endpoint is read-only and guarded by the `WEATHER_VIEW` permission via the
RBAC middleware path policy.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps.auth import CurrentUser
from app.api.deps.container import get_weather_service
from app.schemas.common import ApiResponse
from app.schemas.intelligence import WeatherRead
from app.services.weather_service import WeatherService

router = APIRouter(prefix="/weather", tags=["weather"])


@router.get(
    "", response_model=ApiResponse[WeatherRead], summary="Get weather for a location"
)
async def get_weather(
    _: CurrentUser,
    weather: Annotated[WeatherService, Depends(get_weather_service)],
    latitude: float = Query(ge=-90, le=90),
    longitude: float = Query(ge=-180, le=180),
) -> ApiResponse[WeatherRead]:
    """Return current weather, served from cache when available."""
    snapshot = await weather.get_weather(latitude, longitude)
    return ApiResponse(
        data=WeatherRead(
            latitude=snapshot.latitude,
            longitude=snapshot.longitude,
            temperature_c=snapshot.temperature_c,
            precipitation_mm=snapshot.precipitation_mm,
            wind_kmh=snapshot.wind_kmh,
            humidity_pct=snapshot.humidity_pct,
            condition=snapshot.condition,
            source=snapshot.source,
            forecast=snapshot.forecast,
            is_mock=snapshot.is_mock,
            fetched_at=snapshot.fetched_at,
            expires_at=snapshot.expires_at,
        )
    )
