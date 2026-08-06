"""SQLAlchemy async repository for cold-chain alerts."""

import builtins
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.domain.entities.intelligence import ColdAlert
from app.models.alert import ColdAlert as AlertModel
from app.repositories.base import to_alert_entity


class SqlAlchemyAlertRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, entity: ColdAlert) -> ColdAlert:
        self._session.add(
            AlertModel(
                id=entity.alert_id,
                shipment_id=entity.shipment_id,
                container_id=entity.container_id,
                severity=entity.severity,
                alert_type=entity.alert_type,
                message=entity.message,
                status=entity.status,
                acknowledged_by=entity.acknowledged_by,
                acknowledged_at=entity.acknowledged_at,
            )
        )
        await self._session.flush()
        return entity

    async def get(self, alert_id: UUID) -> ColdAlert | None:
        model = await self._session.get(AlertModel, alert_id)
        return to_alert_entity(model) if model else None

    async def list(self, status: str | None = None) -> builtins.list[ColdAlert]:
        query = select(AlertModel).order_by(AlertModel.created_at.desc())
        if status:
            query = query.where(AlertModel.status == status)
        result = await self._session.execute(query)
        return [to_alert_entity(model) for model in result.scalars().all()]

    async def list_for_shipment(self, shipment_id: UUID) -> builtins.list[ColdAlert]:
        result = await self._session.execute(
            select(AlertModel)
            .where(AlertModel.shipment_id == shipment_id)
            .order_by(AlertModel.created_at.desc())
        )
        return [to_alert_entity(model) for model in result.scalars().all()]

    async def count(
        self,
        *,
        shipment_id: UUID | None = None,
        container_id: UUID | None = None,
        severity: str | None = None,
        status: str | None = None,
    ) -> int:
        query = self._apply_filters(
            select(func.count(AlertModel.id)),
            shipment_id=shipment_id,
            container_id=container_id,
            severity=severity,
            status=status,
        )
        result = await self._session.execute(query)
        return int(result.scalar_one())

    async def list_paginated(
        self,
        *,
        shipment_id: UUID | None = None,
        container_id: UUID | None = None,
        severity: str | None = None,
        status: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> builtins.list[ColdAlert]:
        query = self._apply_filters(
            select(AlertModel),
            shipment_id=shipment_id,
            container_id=container_id,
            severity=severity,
            status=status,
        )
        query = query.order_by(AlertModel.created_at.desc()).offset(offset).limit(limit)
        result = await self._session.execute(query)
        return [to_alert_entity(model) for model in result.scalars().all()]

    async def update(self, entity: ColdAlert) -> ColdAlert:
        model = await self._session.get(AlertModel, entity.alert_id)
        if model is None:
            raise NotFoundError("Alert not found")
        model.severity = entity.severity
        model.alert_type = entity.alert_type
        model.message = entity.message
        model.status = entity.status
        model.acknowledged_by = entity.acknowledged_by
        model.acknowledged_at = entity.acknowledged_at
        await self._session.flush()
        return entity

    async def acknowledge(self, alert_id: UUID, user_id: UUID) -> ColdAlert | None:
        model = await self._session.get(AlertModel, alert_id)
        if model is None:
            return None
        model.status = "acknowledged"
        model.acknowledged_by = user_id
        model.acknowledged_at = datetime.now(UTC)
        await self._session.flush()
        return to_alert_entity(model)

    async def delete(self, alert_id: UUID) -> ColdAlert | None:
        model = await self._session.get(AlertModel, alert_id)
        if model is None:
            return None
        entity = to_alert_entity(model)
        await self._session.delete(model)
        await self._session.flush()
        return entity

    def _apply_filters(
        self,
        query: Select,
        *,
        shipment_id: UUID | None,
        container_id: UUID | None,
        severity: str | None,
        status: str | None,
    ) -> Select:
        if shipment_id is not None:
            query = query.where(AlertModel.shipment_id == shipment_id)
        if container_id is not None:
            query = query.where(AlertModel.container_id == container_id)
        if severity:
            query = query.where(AlertModel.severity == severity.strip().lower())
        if status:
            query = query.where(AlertModel.status == status.strip().lower())
        return query
