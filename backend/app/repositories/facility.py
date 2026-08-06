"""SQLAlchemy async repositories for facilities (warehouse / PHC)."""

import builtins
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
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

    async def update(self, entity: Warehouse) -> Warehouse:
        model = await self._session.get(WarehouseModel, entity.warehouse_id)
        if model is None:
            raise NotFoundError("Warehouse not found")
        model.name = entity.name
        model.code = entity.code
        model.latitude = entity.latitude
        model.longitude = entity.longitude
        model.address = entity.address
        model.capacity = entity.capacity
        await self._session.flush()
        return entity

    async def get(self, warehouse_id: UUID) -> Warehouse | None:
        result = await self._session.execute(
            select(WarehouseModel).where(
                WarehouseModel.id == warehouse_id,
                WarehouseModel.is_deleted.is_(False),
            )
        )
        model = result.scalar_one_or_none()
        return to_warehouse_entity(model) if model else None

    async def get_by_code(self, code: str) -> Warehouse | None:
        result = await self._session.execute(
            select(WarehouseModel).where(WarehouseModel.code == code.strip().upper())
        )
        model = result.scalar_one_or_none()
        return to_warehouse_entity(model) if model else None

    async def list(self) -> builtins.list[Warehouse]:
        result = await self._session.execute(
            select(WarehouseModel)
            .where(WarehouseModel.is_deleted.is_(False))
            .order_by(WarehouseModel.name)
        )
        return [to_warehouse_entity(model) for model in result.scalars().all()]

    async def count(
        self,
        *,
        search: str | None = None,
        capacity_min: int | None = None,
        capacity_max: int | None = None,
    ) -> int:
        query = self._apply_filters(
            select(func.count(WarehouseModel.id)),
            search=search,
            capacity_min=capacity_min,
            capacity_max=capacity_max,
        ).where(WarehouseModel.is_deleted.is_(False))
        result = await self._session.execute(query)
        return int(result.scalar_one())

    async def list_paginated(
        self,
        *,
        search: str | None = None,
        capacity_min: int | None = None,
        capacity_max: int | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> builtins.list[Warehouse]:
        query = self._apply_filters(
            select(WarehouseModel),
            search=search,
            capacity_min=capacity_min,
            capacity_max=capacity_max,
        ).where(WarehouseModel.is_deleted.is_(False))
        query = query.order_by(WarehouseModel.name).offset(offset).limit(limit)
        result = await self._session.execute(query)
        return [to_warehouse_entity(model) for model in result.scalars().all()]

    async def soft_delete(self, warehouse_id: UUID) -> Warehouse | None:
        model = await self._session.get(WarehouseModel, warehouse_id)
        if model is None:
            return None
        model.is_deleted = True
        model.deleted_at = datetime.now(UTC)
        await self._session.flush()
        return to_warehouse_entity(model)

    def _apply_filters(
        self,
        query: Select,
        *,
        search: str | None,
        capacity_min: int | None,
        capacity_max: int | None,
    ) -> Select:
        if search:
            pattern = f"%{search.strip().lower()}%"
            query = query.where(
                or_(
                    WarehouseModel.name.ilike(pattern),
                    WarehouseModel.code.ilike(pattern),
                )
            )
        if capacity_min is not None:
            query = query.where(WarehouseModel.capacity >= capacity_min)
        if capacity_max is not None:
            query = query.where(WarehouseModel.capacity <= capacity_max)
        return query


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
            select(PhCentreModel).where(
                PhCentreModel.id == phc_id,
                PhCentreModel.is_deleted.is_(False),
            )
        )
        model = result.scalar_one_or_none()
        return to_phc_entity(model) if model else None

    async def get_by_code(self, code: str) -> PrimaryHealthCentre | None:
        result = await self._session.execute(
            select(PhCentreModel).where(PhCentreModel.code == code.strip().upper())
        )
        model = result.scalar_one_or_none()
        return to_phc_entity(model) if model else None

    async def list(self) -> builtins.list[PrimaryHealthCentre]:
        result = await self._session.execute(
            select(PhCentreModel)
            .where(PhCentreModel.is_deleted.is_(False))
            .order_by(PhCentreModel.name)
        )
        return [to_phc_entity(model) for model in result.scalars().all()]

    async def update(self, entity: PrimaryHealthCentre) -> PrimaryHealthCentre:
        model = await self._session.get(PhCentreModel, entity.phc_id)
        if model is None:
            raise NotFoundError("Primary health centre not found")
        model.name = entity.name
        model.code = entity.code
        model.district = entity.district
        model.state = entity.state
        model.latitude = entity.latitude
        model.longitude = entity.longitude
        model.contact = entity.contact
        model.capacity = entity.capacity
        model.priority_level = entity.priority_level
        await self._session.flush()
        return entity

    async def count(
        self,
        *,
        search: str | None = None,
        state: str | None = None,
        capacity_min: int | None = None,
        capacity_max: int | None = None,
        priority_level: int | None = None,
    ) -> int:
        query = self._apply_filters(
            select(func.count(PhCentreModel.id)),
            search=search,
            state=state,
            capacity_min=capacity_min,
            capacity_max=capacity_max,
            priority_level=priority_level,
        ).where(PhCentreModel.is_deleted.is_(False))
        result = await self._session.execute(query)
        return int(result.scalar_one())

    async def list_paginated(
        self,
        *,
        search: str | None = None,
        state: str | None = None,
        capacity_min: int | None = None,
        capacity_max: int | None = None,
        priority_level: int | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> builtins.list[PrimaryHealthCentre]:
        query = self._apply_filters(
            select(PhCentreModel),
            search=search,
            state=state,
            capacity_min=capacity_min,
            capacity_max=capacity_max,
            priority_level=priority_level,
        ).where(PhCentreModel.is_deleted.is_(False))
        query = query.order_by(PhCentreModel.name).offset(offset).limit(limit)
        result = await self._session.execute(query)
        return [to_phc_entity(model) for model in result.scalars().all()]

    async def soft_delete(self, phc_id: UUID) -> PrimaryHealthCentre | None:
        model = await self._session.get(PhCentreModel, phc_id)
        if model is None:
            return None
        model.is_deleted = True
        model.deleted_at = datetime.now(UTC)
        await self._session.flush()
        return to_phc_entity(model)

    def _apply_filters(
        self,
        query: Select,
        *,
        search: str | None,
        state: str | None,
        capacity_min: int | None,
        capacity_max: int | None,
        priority_level: int | None,
    ) -> Select:
        if search:
            pattern = f"%{search.strip().lower()}%"
            query = query.where(
                or_(
                    PhCentreModel.name.ilike(pattern),
                    PhCentreModel.code.ilike(pattern),
                    PhCentreModel.district.ilike(pattern),
                )
            )
        if state:
            query = query.where(PhCentreModel.state == state.strip())
        if capacity_min is not None:
            query = query.where(PhCentreModel.capacity >= capacity_min)
        if capacity_max is not None:
            query = query.where(PhCentreModel.capacity <= capacity_max)
        if priority_level is not None:
            query = query.where(PhCentreModel.priority_level == priority_level)
        return query
