"""SQLAlchemy async repositories for shipments and predictions."""

import builtins
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.domain.entities.intelligence import Prediction
from app.domain.entities.shipment import Shipment
from app.models.prediction import Prediction as PredictionModel
from app.models.shipment import Shipment as ShipmentModel
from app.repositories.base import to_prediction_entity, to_shipment_entity

_SORTABLE_COLUMNS = {
    "created_at": ShipmentModel.created_at,
    "tracking_code": ShipmentModel.tracking_code,
    "status": ShipmentModel.status_state,
    "priority": ShipmentModel.priority,
    "vaccine_name": ShipmentModel.vaccine_name,
    "estimated_delivery_at": ShipmentModel.estimated_delivery_at,
}


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
            select(ShipmentModel).where(
                ShipmentModel.id == shipment_id,
                ShipmentModel.is_deleted.is_(False),
            )
        )
        model = result.scalar_one_or_none()
        return to_shipment_entity(model) if model else None

    async def get_by_tracking_code(self, tracking_code: str) -> Shipment | None:
        result = await self._session.execute(
            select(ShipmentModel).where(
                ShipmentModel.tracking_code == tracking_code.strip().upper()
            )
        )
        model = result.scalar_one_or_none()
        return to_shipment_entity(model) if model else None

    async def list(self) -> list[Shipment]:
        result = await self._session.execute(
            select(ShipmentModel)
            .where(ShipmentModel.is_deleted.is_(False))
            .order_by(ShipmentModel.created_at.desc())
        )
        return [to_shipment_entity(model) for model in result.scalars().all()]

    async def update(self, entity: Shipment) -> Shipment:
        model = await self._session.get(ShipmentModel, entity.shipment_id)
        if model is None:
            raise NotFoundError("Shipment not found")
        model.vaccine_name = entity.vaccine_name
        model.dose_count = entity.dose_count
        model.priority = entity.priority.value
        model.temperature_min = entity.temperature_min
        model.temperature_max = entity.temperature_max
        model.warehouse_id = entity.warehouse_id
        model.destination_id = entity.destination_id
        model.container_id = entity.container_id
        model.driver_id = entity.driver_id
        model.status_state = entity.status.value
        model.dispatched_at = entity.dispatched_at
        model.delivered_at = entity.delivered_at
        model.estimated_delivery_at = entity.estimated_delivery_at
        await self._session.flush()
        return entity

    async def count(
        self,
        *,
        search: str | None = None,
        shipment_id: UUID | None = None,
        tracking_code: str | None = None,
        origin: UUID | None = None,
        destination: UUID | None = None,
        status: str | None = None,
        priority: str | None = None,
        vaccine_type: str | None = None,
        created_after: datetime | None = None,
        created_before: datetime | None = None,
        expected_delivery_after: datetime | None = None,
        expected_delivery_before: datetime | None = None,
    ) -> int:
        query = self._apply_filters(
            select(func.count(ShipmentModel.id)),
            search=search,
            shipment_id=shipment_id,
            tracking_code=tracking_code,
            origin=origin,
            destination=destination,
            status=status,
            priority=priority,
            vaccine_type=vaccine_type,
            created_after=created_after,
            created_before=created_before,
            expected_delivery_after=expected_delivery_after,
            expected_delivery_before=expected_delivery_before,
        ).where(ShipmentModel.is_deleted.is_(False))
        result = await self._session.execute(query)
        return int(result.scalar_one())

    async def list_paginated(
        self,
        *,
        search: str | None = None,
        shipment_id: UUID | None = None,
        tracking_code: str | None = None,
        origin: UUID | None = None,
        destination: UUID | None = None,
        status: str | None = None,
        priority: str | None = None,
        vaccine_type: str | None = None,
        created_after: datetime | None = None,
        created_before: datetime | None = None,
        expected_delivery_after: datetime | None = None,
        expected_delivery_before: datetime | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        offset: int = 0,
        limit: int = 20,
    ) -> builtins.list[Shipment]:
        query = self._apply_filters(
            select(ShipmentModel),
            search=search,
            shipment_id=shipment_id,
            tracking_code=tracking_code,
            origin=origin,
            destination=destination,
            status=status,
            priority=priority,
            vaccine_type=vaccine_type,
            created_after=created_after,
            created_before=created_before,
            expected_delivery_after=expected_delivery_after,
            expected_delivery_before=expected_delivery_before,
        ).where(ShipmentModel.is_deleted.is_(False))
        column = _SORTABLE_COLUMNS.get(sort_by, ShipmentModel.created_at)
        direction = column.asc() if sort_order == "asc" else column.desc()
        query = query.order_by(direction).offset(offset).limit(limit)
        result = await self._session.execute(query)
        return [to_shipment_entity(model) for model in result.scalars().all()]

    async def soft_delete(self, shipment_id: UUID) -> Shipment | None:
        model = await self._session.get(ShipmentModel, shipment_id)
        if model is None:
            return None
        model.is_deleted = True
        model.deleted_at = datetime.now(UTC)
        await self._session.flush()
        return to_shipment_entity(model)

    def _apply_filters(
        self,
        query: Select,
        *,
        search: str | None,
        shipment_id: UUID | None,
        tracking_code: str | None,
        origin: UUID | None,
        destination: UUID | None,
        status: str | None,
        priority: str | None,
        vaccine_type: str | None,
        created_after: datetime | None,
        created_before: datetime | None,
        expected_delivery_after: datetime | None,
        expected_delivery_before: datetime | None,
    ) -> Select:
        if search:
            pattern = f"%{search.strip().lower()}%"
            query = query.where(
                or_(
                    ShipmentModel.tracking_code.ilike(pattern),
                    ShipmentModel.vaccine_name.ilike(pattern),
                )
            )
        if shipment_id is not None:
            query = query.where(ShipmentModel.id == shipment_id)
        if tracking_code:
            query = query.where(
                ShipmentModel.tracking_code.ilike(f"%{tracking_code.strip().upper()}%")
            )
        if origin is not None:
            query = query.where(ShipmentModel.warehouse_id == origin)
        if destination is not None:
            query = query.where(ShipmentModel.destination_id == destination)
        if status:
            query = query.where(ShipmentModel.status_state == status.strip().lower())
        if priority:
            query = query.where(ShipmentModel.priority == priority.strip().lower())
        if vaccine_type:
            query = query.where(
                ShipmentModel.vaccine_name.ilike(f"%{vaccine_type.strip()}%")
            )
        if created_after is not None:
            query = query.where(ShipmentModel.created_at >= created_after)
        if created_before is not None:
            query = query.where(ShipmentModel.created_at <= created_before)
        if expected_delivery_after is not None:
            query = query.where(
                ShipmentModel.estimated_delivery_at >= expected_delivery_after
            )
        if expected_delivery_before is not None:
            query = query.where(
                ShipmentModel.estimated_delivery_at <= expected_delivery_before
            )
        return query


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

    async def get(self, prediction_id: UUID) -> Prediction | None:
        model = await self._session.get(PredictionModel, prediction_id)
        return to_prediction_entity(model) if model else None

    async def list_for_shipment(self, shipment_id: UUID) -> builtins.list[Prediction]:
        result = await self._session.execute(
            select(PredictionModel)
            .where(PredictionModel.shipment_id == shipment_id)
            .order_by(PredictionModel.created_at.desc())
        )
        return [to_prediction_entity(model) for model in result.scalars().all()]

    async def latest_for_shipment(self, shipment_id: UUID) -> Prediction | None:
        result = await self._session.execute(
            select(PredictionModel)
            .where(PredictionModel.shipment_id == shipment_id)
            .order_by(PredictionModel.created_at.desc())
            .limit(1)
        )
        model = result.scalar_one_or_none()
        return to_prediction_entity(model) if model else None

    async def count(
        self,
        *,
        shipment_id: UUID | None = None,
        risk_level: str | None = None,
        model_version: str | None = None,
    ) -> int:
        query = self._apply_filters(
            select(func.count(PredictionModel.id)),
            shipment_id=shipment_id,
            risk_level=risk_level,
            model_version=model_version,
        )
        result = await self._session.execute(query)
        return int(result.scalar_one())

    async def list_paginated(
        self,
        *,
        shipment_id: UUID | None = None,
        risk_level: str | None = None,
        model_version: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> builtins.list[Prediction]:
        query = self._apply_filters(
            select(PredictionModel),
            shipment_id=shipment_id,
            risk_level=risk_level,
            model_version=model_version,
        )
        query = (
            query.order_by(PredictionModel.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(query)
        return [to_prediction_entity(model) for model in result.scalars().all()]

    async def update(self, entity: Prediction) -> Prediction:
        model = await self._session.get(PredictionModel, entity.prediction_id)
        if model is None:
            raise NotFoundError("Prediction not found")
        model.excursion_risk = entity.excursion_risk
        model.risk_level = entity.risk_level
        model.confidence = entity.confidence
        model.expected_min_temp = entity.expected_min_temp
        model.expected_max_temp = entity.expected_max_temp
        model.model_version = entity.model_version
        model.features = entity.features
        model.explanations = entity.explanations
        await self._session.flush()
        return entity

    async def delete(self, prediction_id: UUID) -> Prediction | None:
        model = await self._session.get(PredictionModel, prediction_id)
        if model is None:
            return None
        entity = to_prediction_entity(model)
        await self._session.delete(model)
        await self._session.flush()
        return entity

    def _apply_filters(
        self,
        query: Select,
        *,
        shipment_id: UUID | None,
        risk_level: str | None,
        model_version: str | None,
    ) -> Select:
        if shipment_id is not None:
            query = query.where(PredictionModel.shipment_id == shipment_id)
        if risk_level:
            query = query.where(
                PredictionModel.risk_level == risk_level.strip().lower()
            )
        if model_version:
            query = query.where(PredictionModel.model_version == model_version.strip())
        return query
