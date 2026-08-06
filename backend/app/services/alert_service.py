"""Alert service: CRUD, acknowledgement and lifecycle for cold-chain alerts."""

import builtins
from uuid import UUID

from app.core.exceptions import NotFoundError, ValidationError
from app.domain.entities.intelligence import ColdAlert
from app.domain.repositories import (
    AlertRepository,
    ContainerRepository,
    ShipmentRepository,
)
from app.schemas.alert import AlertCreate, AlertUpdate


class AlertService:
    def __init__(
        self,
        alert_repo: AlertRepository,
        shipment_repo: ShipmentRepository,
        container_repo: ContainerRepository,
    ) -> None:
        self._alerts = alert_repo
        self._shipments = shipment_repo
        self._containers = container_repo

    async def create(self, payload: AlertCreate) -> ColdAlert:
        if payload.shipment_id is not None:
            shipment = await self._shipments.get(payload.shipment_id)
            if shipment is None:
                raise NotFoundError("Shipment not found")
        if payload.container_id is not None:
            container = await self._containers.get(payload.container_id)
            if container is None:
                raise NotFoundError("Container not found")
        try:
            entity = ColdAlert.create(
                severity=payload.severity,
                alert_type=payload.alert_type,
                message=payload.message,
                shipment_id=payload.shipment_id,
                container_id=payload.container_id,
            )
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        return await self._alerts.create(entity)

    async def get(self, alert_id: UUID) -> ColdAlert:
        entity = await self._alerts.get(alert_id)
        if entity is None:
            raise NotFoundError("Alert not found")
        return entity

    async def list(
        self,
        *,
        shipment_id: UUID | None = None,
        container_id: UUID | None = None,
        severity: str | None = None,
        status: str | None = None,
        page: int = 1,
        size: int = 20,
    ) -> tuple[builtins.list[ColdAlert], int]:
        offset = (page - 1) * size
        items = await self._alerts.list_paginated(
            shipment_id=shipment_id,
            container_id=container_id,
            severity=severity,
            status=status,
            offset=offset,
            limit=size,
        )
        total = await self._alerts.count(
            shipment_id=shipment_id,
            container_id=container_id,
            severity=severity,
            status=status,
        )
        return items, total

    async def history(self, shipment_id: UUID) -> builtins.list[ColdAlert]:
        shipment = await self._shipments.get(shipment_id)
        if shipment is None:
            raise NotFoundError("Shipment not found")
        return await self._alerts.list_for_shipment(shipment_id)

    async def update(self, alert_id: UUID, payload: AlertUpdate) -> ColdAlert:
        entity = await self.get(alert_id)
        try:
            entity.update(
                severity=payload.severity,
                alert_type=payload.alert_type,
                message=payload.message,
            )
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        return await self._alerts.update(entity)

    async def acknowledge(self, alert_id: UUID, user_id: UUID) -> ColdAlert:
        entity = await self.get(alert_id)
        try:
            entity.acknowledge(user_id)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        acknowledged = await self._alerts.acknowledge(alert_id, user_id)
        if acknowledged is None:
            raise NotFoundError("Alert not found")
        return acknowledged

    async def resolve(self, alert_id: UUID) -> ColdAlert:
        entity = await self.get(alert_id)
        try:
            entity.resolve()
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        return await self._alerts.update(entity)

    async def delete(self, alert_id: UUID) -> ColdAlert:
        entity = await self.get(alert_id)
        deleted = await self._alerts.delete(alert_id)
        if deleted is None:
            raise NotFoundError("Alert not found")
        return entity
