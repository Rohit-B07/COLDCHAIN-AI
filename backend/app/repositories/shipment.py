"""SQLAlchemy async repositories for shipments, predictions and weather cache."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.intelligence import Prediction, WeatherSnapshot
from app.domain.entities.shipment import Shipment
from app.models.prediction import Prediction as PredictionModel
from app.models.shipment import Shipment as ShipmentModel
from app.models.weather import WeatherCache as WeatherCacheModel
from app.repositories.base import to_prediction_entity, to_shipment_entity, to_weather_entity


class SqlAlchemyShipmentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, entity: Shipment) -> Shipment:
        model = ShipmentModel(
            id=entity.shipment_id,
            tracking_code=entity.tracking_code,
            vaccine_name=entity.vaccine_name,
            dose_count=entity.dose_count,
            priority=entity.priority.value,
            temperature_min=entity.temperature_min,
            temperature_max=entity.temperature_max,
            warehouse_id=entity.warehouse_id,
            destination_id=entity.destination_id,
            container_id=entity.container_id,
            driver_id=entity.driver_id,
            status_state=entity.status.value,
            dispatched_at=entity.dispatched_at,
            delivered_at=entity.delivered_at,
            estimated_delivery_at=entity.estimated_delivery_at,
        )
        self._session.add(model)
        await self._session.flush()
        return entity

    async def get(self, shipment_id: UUID) -> Shipment | None:
        result = await self._session.execute(
            select(ShipmentModel).where(ShipmentModel.id == shipment_id)
        )
        model = result.scalar_one_or_none()
        return to_shipment_entity(model) if model else None

    async def list(self) -> list[Shipment]:
        result = await self._session.execute(
            select(ShipmentModel).order_by(ShipmentModel.created_at.desc())
        )
        return [to_shipment_entity(model) for model in result.scalars().all()]

    async def update(self, entity: Shipment) -> Shipment:
        result = await self._session.execute(
            select(ShipmentModel).where(ShipmentModel.id == entity.shipment_id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return entity
        model.priority = entity.priority.value
        model.temperature_min = entity.temperature_min
        model.temperature_max = entity.temperature_max
        model.container_id = entity.container_id
        model.driver_id = entity.driver_id
        model.status_state = entity.status.value
        model.dispatched_at = entity.dispatched_at
        model.delivered_at = entity.delivered_at
        model.estimated_delivery_at = entity.estimated_delivery_at
        await self._session.flush()
        return entity


class SqlAlchemyPredictionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, entity: Prediction) -> Prediction:
        self._session.add(
            PredictionModel(
                id=entity.prediction_id,
                shipment_id=entity.shipment_id,
                excursion_risk=entity.excursion_risk,
                risk_level=entity.risk_level,
                confidence=entity.confidence,
                expected_min_temp=entity.expected_min_temp,
                expected_max_temp=entity.expected_max_temp,
                model_version=entity.model_version,
                features=entity.features,
                explanations=entity.explanations,
                valid_until=entity.created_at,
            )
        )
        await self._session.flush()
        return entity

    async def latest_for_shipment(self, shipment_id: UUID) -> Prediction | None:
        result = await self._session.execute(
            select(PredictionModel)
            .where(PredictionModel.shipment_id == shipment_id)
            .order_by(PredictionModel.created_at.desc())
            .limit(1)
        )
        model = result.scalar_one_or_none()
        return to_prediction_entity(model) if model else None


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
                    forecast={},
                    is_mock=snapshot.is_mock,
                    fetched_at=now,
                    expires_at=now + timedelta(hours=1),
                )
            )
        else:
            model.temperature_c = snapshot.temperature_c
            model.precipitation_mm = snapshot.precipitation_mm
            model.wind_kmh = snapshot.wind_kmh
            model.humidity_pct = snapshot.humidity_pct
            model.condition = snapshot.condition
            model.is_mock = snapshot.is_mock
            model.fetched_at = now
            model.expires_at = now + timedelta(hours=1)
        await self._session.flush()