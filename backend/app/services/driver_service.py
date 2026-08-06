"""Driver management service.

Coordinates driver CRUD plus the dedicated status and vehicle-assignment
workflows. Business rules live on the ``Driver`` entity (phone/license format,
status transitions, local assignment invariants); cross-aggregate rules
(vehicle must exist and be active, one active driver per vehicle) are enforced
here against the injected repositories.
"""

from uuid import UUID

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.domain.entities.logistics import Driver
from app.domain.repositories import DriverRepository, VehicleRepository
from app.schemas.driver import DriverCreate, DriverStatusUpdate, DriverUpdate


class DriverService:
    def __init__(
        self, driver_repo: DriverRepository, vehicle_repo: VehicleRepository
    ) -> None:
        self._drivers = driver_repo
        self._vehicles = vehicle_repo

    async def create(self, payload: DriverCreate) -> Driver:
        try:
            entity = Driver.create(
                name=payload.name,
                phone=payload.phone,
                license_number=payload.license_number,
            )
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        if await self._drivers.get_by_phone(entity.phone):
            raise ConflictError("A driver with this phone number already exists")
        if await self._drivers.get_by_license(entity.license_number):
            raise ConflictError("A driver with this license number already exists")
        return await self._drivers.create(entity)

    async def get(self, driver_id: UUID) -> Driver:
        entity = await self._drivers.get(driver_id)
        if entity is None:
            raise NotFoundError("Driver not found")
        return entity

    async def list(
        self,
        *,
        search: str | None,
        status: str | None,
        page: int,
        size: int,
    ) -> tuple[list[Driver], int]:
        offset = (page - 1) * size
        total = await self._drivers.count(search=search, status=status)
        items = await self._drivers.list_paginated(
            search=search, status=status, offset=offset, limit=size
        )
        return items, total

    async def update(self, driver_id: UUID, payload: DriverUpdate) -> Driver:
        entity = await self.get(driver_id)
        try:
            entity.update(
                name=payload.name,
                phone=payload.phone,
                license_number=payload.license_number,
            )
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        await self._ensure_unique(entity)
        return await self._drivers.update(entity)

    async def change_status(
        self, driver_id: UUID, payload: DriverStatusUpdate
    ) -> Driver:
        entity = await self.get(driver_id)
        try:
            entity.change_status(payload.status)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        return await self._drivers.update(entity)

    async def assign_vehicle(self, driver_id: UUID, vehicle_id: UUID) -> Driver:
        entity = await self.get(driver_id)
        vehicle = await self._vehicles.get(vehicle_id)
        if vehicle is None:
            raise NotFoundError("Vehicle not found")
        if vehicle.status != "active":
            raise ValidationError(
                "Cannot assign a driver to a vehicle that is not active"
            )
        current = await self._drivers.get_assigned_driver(vehicle_id)
        if current is not None and current.driver_id != driver_id:
            raise ConflictError("Vehicle already has an assigned driver")
        try:
            entity.assign_vehicle(vehicle_id)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        return await self._drivers.update(entity)

    async def unassign_vehicle(self, driver_id: UUID) -> Driver:
        entity = await self.get(driver_id)
        entity.unassign_vehicle()
        return await self._drivers.update(entity)

    async def delete(self, driver_id: UUID) -> Driver:
        entity = await self.get(driver_id)
        entity.soft_delete()
        await self._drivers.soft_delete(driver_id)
        return entity

    async def _ensure_unique(self, entity: Driver) -> None:
        phone_holder = await self._drivers.get_by_phone(entity.phone)
        if phone_holder is not None and phone_holder.driver_id != entity.driver_id:
            raise ConflictError("A driver with this phone number already exists")
        license_holder = await self._drivers.get_by_license(entity.license_number)
        if license_holder is not None and license_holder.driver_id != entity.driver_id:
            raise ConflictError("A driver with this license number already exists")
