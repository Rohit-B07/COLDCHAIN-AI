"""SQLAlchemy async repositories for facilities (warehouse / PHC)."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.facility import PrimaryHealthCentre, Warehouse
from app.models.facility import (
    PrimaryHealthCentre as PhCentreModel,
    Warehouse as WarehouseModel,
)
from app.repositories.base import to_phc_entity, to_warehouse_entity


class SqlAlchemyWarehouseRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, entity: Warehouse) -> Warehouse:
        self._session.add(
            WarehouseModel(
                id=entity.warehouse_id,
                name=entity.name,
                code=entity.code,
                latitude=entity.latitude,
                longitude=entity.longitude,
                address=entity.address,
                capacity=entity.capacity,
            )
        )
        await self._session.flush()
        return entity

    async def get(self, warehouse_id: UUID) -> Warehouse | None:
        result = await self._session.execute(
            select(WarehouseModel).where(WarehouseModel.id == warehouse_id)
        )
        model = result.scalar_one_or_none()
        return to_warehouse_entity(model) if model else None

    async def list(self) -> list[Warehouse]:
        result = await self._session.execute(
            select(WarehouseModel).order_by(WarehouseModel.name)
        )
        return [to_warehouse_entity(model) for model in result.scalars().all()]


class SqlAlchemyPhCentreRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, entity: PrimaryHealthCentre) -> PrimaryHealthCentre:
        self._session.add(
            PhCentreModel(
                id=entity.phc_id,
                name=entity.name,
                code=entity.code,
                district=entity.district,
                state=entity.state,
                latitude=entity.latitude,
                longitude=entity.longitude,
                contact=entity.contact,
                capacity=entity.capacity,
                priority_level=entity.priority_level,
            )
        )
        await self._session.flush()
        return entity

    async def get(self, phc_id: UUID) -> PrimaryHealthCentre | None:
        result = await self._session.execute(
            select(PhCentreModel).where(PhCentreModel.id == phc_id)
        )
        model = result.scalar_one_or_none()
        return to_phc_entity(model) if model else None

    async def list(self) -> list[PrimaryHealthCentre]:
        result = await self._session.execute(
            select(PhCentreModel).order_by(PhCentreModel.name)
        )
        return [to_phc_entity(model) for model in result.scalars().all()]
