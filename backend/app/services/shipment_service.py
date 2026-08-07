"""Shipment application service.

Coordinates shipment CRUD plus the dedicated dispatch and cancel workflows.
Business rules live on the ``Shipment`` entity (tracking code format, dose and
temperature bounds, status transitions); cross-aggregate rules (warehouse and
destination must exist, container and driver must be usable) are enforced here
against the injected repositories.
"""

from datetime import datetime
from uuid import UUID

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.domain.entities.shipment import Shipment
from app.domain.repositories import (
    ContainerRepository,
    DriverRepository,
    PhCentreRepository,
    ShipmentRepository,
    WarehouseRepository,
)
from app.schemas.shipment import DispatchRequest, ShipmentCreate, ShipmentUpdate


class ShipmentService:
    def __init__(
        self,
        shipment_repo: ShipmentRepository,
        warehouse_repo: WarehouseRepository,
        phc_repo: PhCentreRepository,
        container_repo: ContainerRepository,
        driver_repo: DriverRepository,
    ) -> None:
        self._shipments = shipment_repo
        self._warehouses = warehouse_repo
        self._phcs = phc_repo
        self._containers = container_repo
        self._drivers = driver_repo

    async def create(self, payload: ShipmentCreate) -> Shipment:
        warehouse = await self._warehouses.get(payload.warehouse_id)
        if warehouse is None or warehouse.is_deleted:
            raise NotFoundError("Warehouse not found")
        destination = await self._phcs.get(payload.destination_id)
        if destination is None or destination.is_deleted:
            raise NotFoundError("Primary health centre not found")
        if payload.container_id is not None:
            container = await self._containers.get(payload.container_id)
            if container is None:
                raise NotFoundError("Container not found")
        if payload.driver_id is not None:
            driver = await self._drivers.get(payload.driver_id)
            if driver is None:
                raise NotFoundError("Driver not found")
            if driver.status == "on_leave":
                raise ValidationError("Cannot assign a driver on leave to a shipment")
        try:
            entity = Shipment.create(
                tracking_code=Shipment.generate_tracking_code(),
                vaccine_name=payload.vaccine_name,
                dose_count=payload.dose_count,
                warehouse_id=payload.warehouse_id,
                destination_id=payload.destination_id,
                priority=payload.priority,
                temperature_min=payload.temperature_min,
                temperature_max=payload.temperature_max,
                container_id=payload.container_id,
                driver_id=payload.driver_id,
            )
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        existing = await self._shipments.get_by_tracking_code(entity.tracking_code)
        if existing is not None:
            raise ConflictError(
                f"A shipment with tracking code {entity.tracking_code!r} already exists"
            )
        return await self._shipments.create(entity)

    async def get(self, shipment_id: UUID) -> Shipment:
        entity = await self._shipments.get(shipment_id)
        if entity is None:
            raise NotFoundError("Shipment not found")
        return entity

    async def list(
        self,
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
        sort_by: str,
        sort_order: str,
        page: int,
        size: int,
    ) -> tuple[list[Shipment], int]:
        offset = (page - 1) * size
        total = await self._shipments.count(
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
        )
        items = await self._shipments.list_paginated(
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
            sort_by=sort_by,
            sort_order=sort_order,
            offset=offset,
            limit=size,
        )
        return items, total

    async def update(self, shipment_id: UUID, payload: ShipmentUpdate) -> Shipment:
        entity = await self.get(shipment_id)
        if (
            payload.container_id is not None
            and payload.container_id != entity.container_id
        ):
            container = await self._containers.get(payload.container_id)
            if container is None:
                raise NotFoundError("Container not found")
        if payload.driver_id is not None and payload.driver_id != entity.driver_id:
            driver = await self._drivers.get(payload.driver_id)
            if driver is None:
                raise NotFoundError("Driver not found")
            if driver.status == "on_leave":
                raise ValidationError("Cannot assign a driver on leave to a shipment")
        try:
            entity.update(
                vaccine_name=payload.vaccine_name,
                dose_count=payload.dose_count,
                priority=payload.priority,
                temperature_min=payload.temperature_min,
                temperature_max=payload.temperature_max,
                container_id=payload.container_id,
                driver_id=payload.driver_id,
                estimated_delivery_at=payload.estimated_delivery_at,
            )
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        return await self._shipments.update(entity)

    async def dispatch(self, shipment_id: UUID, payload: DispatchRequest) -> Shipment:
        entity = await self.get(shipment_id)
        container = await self._containers.get(payload.container_id)
        if container is None:
            raise NotFoundError("Container not found")
        if container.status != "idle":
            raise ValidationError("Container is not available for dispatch")
        driver = await self._drivers.get(payload.driver_id)
        if driver is None:
            raise NotFoundError("Driver not found")
        if driver.status == "on_leave":
            raise ValidationError("Cannot dispatch with a driver on leave")
        entity.container_id = payload.container_id
        entity.driver_id = payload.driver_id
        try:
            entity.dispatch()
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        return await self._shipments.update(entity)

    async def cancel(self, shipment_id: UUID) -> Shipment:
        entity = await self.get(shipment_id)
        try:
            entity.cancel()
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        return await self._shipments.update(entity)

    async def delete(self, shipment_id: UUID) -> Shipment:
        entity = await self.get(shipment_id)
        entity.soft_delete()
        await self._shipments.soft_delete(shipment_id)
        return entity
