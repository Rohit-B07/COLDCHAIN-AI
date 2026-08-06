"""SQLAlchemy async repository for cold-chain alerts."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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
            )
        )
        await self._session.flush()
        return entity

    async def list(self, status: str | None = None) -> list[ColdAlert]:
        query = select(AlertModel).order_by(AlertModel.created_at.desc())
        if status:
            query = query.where(AlertModel.status == status)
        result = await self._session.execute(query)
        return [to_alert_entity(model) for model in result.scalars().all()]

    async def acknowledge(self, alert_id: UUID, user_id: UUID) -> ColdAlert | None:
        result = await self._session.execute(
            select(AlertModel).where(AlertModel.id == alert_id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        model.status = "acknowledged"
        model.acknowledged_by = user_id
        model.acknowledged_at = datetime.now(UTC)
        await self._session.flush()
        return to_alert_entity(model)