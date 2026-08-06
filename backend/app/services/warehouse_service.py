"""Warehouse management service.

Coordinates warehouse CRUD, business rules (unique code, code format, capacity
bounds, soft-delete semantics) and paginated/filtered listing. Repository
adapters are injected so the service stays free of persistence and HTTP
concerns.
"""

from uuid import UUID

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.domain.entities.facility import Warehouse
from app.domain.repositories import WarehouseRepository
from app.schemas.warehouse import WarehouseCreate, WarehouseUpdate


class WarehouseService:
    def __init__(self, warehouse_repo: WarehouseRepository) -> None:
        self._repo = warehouse_repo

    async def create(self, payload: WarehouseCreate) -> Warehouse:
        try:
            entity = Warehouse.create(
                name=payload.name,
                code=payload.code,
                latitude=payload.latitude,
                longitude=payload.longitude,
                address=payload.address,
                capacity=payload.capacity,
            )
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        existing = await self._repo.get_by_code(entity.code)
        if existing is not None:
            raise ConflictError(f"A warehouse with code {entity.code!r} already exists")
        return await self._repo.create(entity)

    async def get(self, warehouse_id: UUID) -> Warehouse:
        entity = await self._repo.get(warehouse_id)
        if entity is None:
            raise NotFoundError("Warehouse not found")
        return entity

    async def list(
        self,
        *,
        search: str | None,
        capacity_min: int | None,
        capacity_max: int | None,
        page: int,
        size: int,
    ) -> tuple[list[Warehouse], int]:
        offset = (page - 1) * size
        total = await self._repo.count(
            search=search,
            capacity_min=capacity_min,
            capacity_max=capacity_max,
        )
        items = await self._repo.list_paginated(
            search=search,
            capacity_min=capacity_min,
            capacity_max=capacity_max,
            offset=offset,
            limit=size,
        )
        return items, total

    async def update(self, warehouse_id: UUID, payload: WarehouseUpdate) -> Warehouse:
        entity = await self.get(warehouse_id)
        if payload.code is not None and payload.code.strip().upper() != entity.code:
            existing = await self._repo.get_by_code(payload.code)
            if existing is not None and existing.warehouse_id != warehouse_id:
                raise ConflictError(f"A warehouse with code {payload.code!r} already exists")
        try:
            entity.update(
                name=payload.name,
                code=payload.code,
                latitude=payload.latitude,
                longitude=payload.longitude,
                address=payload.address,
                capacity=payload.capacity,
            )
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        return await self._repo.update(entity)

    async def delete(self, warehouse_id: UUID) -> Warehouse:
        entity = await self.get(warehouse_id)
        entity.soft_delete()
        await self._repo.soft_delete(warehouse_id)
        return entity
