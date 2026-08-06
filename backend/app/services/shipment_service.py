"""Shipment application service."""

from uuid import UUID

from app.core.exceptions import NotFoundError
from app.domain.entities.shipment import Shipment
from app.domain.repositories import ShipmentRepository


class ShipmentService:
    def __init__(self, shipment_repo: ShipmentRepository) -> None:
        self._shipment_repo = shipment_repo

    async def create(self, entity: Shipment) -> Shipment:
        return await self._shipment_repo.create(entity)

    async def get(self, shipment_id: UUID) -> Shipment:
        shipment = await self._shipment_repo.get(shipment_id)
        if shipment is None:
            raise NotFoundError("Shipment not found")
        return shipment

    async def list(self) -> list[Shipment]:
        return await self._shipment_repo.list()

    async def dispatch(self, shipment_id: UUID, container_id: UUID, driver_id: UUID) -> Shipment:
        shipment = await self.get(shipment_id)
        shipment.container_id = container_id
        shipment.driver_id = driver_id
        shipment.dispatch()
        return await self._shipment_repo.update(shipment)