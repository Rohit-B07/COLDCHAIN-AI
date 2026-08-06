"""Vehicle management service.

Coordinates vehicle CRUD plus the dedicated status and maintenance workflows.
Business rules live on the ``Vehicle`` entity (capacity bounds, type and cold
storage consistency, status/maintenance transitions); registration uniqueness
is enforced here against the injected repository.
"""

from uuid import UUID

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.domain.entities.logistics import Vehicle
from app.domain.repositories import VehicleRepository
from app.schemas.vehicle import (
    VehicleCreate,
    VehicleMaintenanceUpdate,
    VehicleStatusUpdate,
    VehicleUpdate,
)


class VehicleService:
    def __init__(self, vehicle_repo: VehicleRepository) -> None:
        self._repo = vehicle_repo

    async def create(self, payload: VehicleCreate) -> Vehicle:
        try:
            entity = Vehicle.create(
                registration_number=payload.registration_number,
                vehicle_type=payload.vehicle_type,
                capacity_kg=payload.capacity_kg,
                is_reefer=payload.is_reefer,
            )
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        existing = await self._repo.get_by_registration(entity.registration_number)
        if existing is not None:
            raise ConflictError(
                f"A vehicle with registration {entity.registration_number!r} already exists"
            )
        return await self._repo.create(entity)

    async def get(self, vehicle_id: UUID) -> Vehicle:
        entity = await self._repo.get(vehicle_id)
        if entity is None:
            raise NotFoundError("Vehicle not found")
        return entity

    async def list(
        self,
        *,
        search: str | None,
        status: str | None,
        vehicle_type: str | None,
        page: int,
        size: int,
    ) -> tuple[list[Vehicle], int]:
        offset = (page - 1) * size
        total = await self._repo.count(
            search=search, status=status, vehicle_type=vehicle_type
        )
        items = await self._repo.list_paginated(
            search=search,
            status=status,
            vehicle_type=vehicle_type,
            offset=offset,
            limit=size,
        )
        return items, total

    async def update(self, vehicle_id: UUID, payload: VehicleUpdate) -> Vehicle:
        entity = await self.get(vehicle_id)
        if (
            payload.registration_number is not None
            and payload.registration_number.strip().upper() != entity.registration_number
        ):
            existing = await self._repo.get_by_registration(
                payload.registration_number
            )
            if existing is not None and existing.vehicle_id != vehicle_id:
                raise ConflictError(
                    f"A vehicle with registration {payload.registration_number!r} already exists"
                )
        try:
            entity.update(
                registration_number=payload.registration_number,
                vehicle_type=payload.vehicle_type,
                capacity_kg=payload.capacity_kg,
                is_reefer=payload.is_reefer,
            )
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        return await self._repo.update(entity)

    async def change_status(
        self, vehicle_id: UUID, payload: VehicleStatusUpdate
    ) -> Vehicle:
        entity = await self.get(vehicle_id)
        try:
            entity.change_status(payload.status)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        return await self._repo.update(entity)

    async def set_maintenance_status(
        self, vehicle_id: UUID, payload: VehicleMaintenanceUpdate
    ) -> Vehicle:
        entity = await self.get(vehicle_id)
        try:
            entity.set_maintenance_status(payload.maintenance_status)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        if payload.last_maintenance_at is not None:
            entity.last_maintenance_at = payload.last_maintenance_at
        if payload.next_maintenance_due_at is not None:
            entity.next_maintenance_due_at = payload.next_maintenance_due_at
        return await self._repo.update(entity)

    async def delete(self, vehicle_id: UUID) -> Vehicle:
        entity = await self.get(vehicle_id)
        entity.soft_delete()
        await self._repo.soft_delete(vehicle_id)
        return entity
