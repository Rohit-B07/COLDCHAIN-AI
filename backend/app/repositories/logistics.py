"""SQLAlchemy async repositories for logistics assets."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.logistics import ColdContainer, Driver, Vehicle
from app.models.logistics import (
    ColdContainer as ContainerModel,
    Driver as DriverModel,
    Vehicle as VehicleModel,
)
from app.repositories.base import (
    to_container_entity,
    to_driver_entity,
    to_vehicle_entity,
)


class SqlAlchemyDriverRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, entity: Driver) -> Driver:
        self._session.add(
            DriverModel(
                id=entity.driver_id,
                name=entity.name,
                phone=entity.phone,
                license_number=entity.license_number,
                status=entity.status,
                vehicle_id=entity.vehicle_id,
            )
        )
        await self._session.flush()
        return entity

    async def get(self, driver_id: UUID) -> Driver | None:
        result = await self._session.execute(
            select(DriverModel).where(DriverModel.id == driver_id)
        )
        model = result.scalar_one_or_none()
        return to_driver_entity(model) if model else None

    async def list(self) -> list[Driver]:
        result = await self._session.execute(select(DriverModel).order_by(DriverModel.name))
        return [to_driver_entity(model) for model in result.scalars().all()]


class SqlAlchemyVehicleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, entity: Vehicle) -> Vehicle:
        self._session.add(
            VehicleModel(
                id=entity.vehicle_id,
                registration_number=entity.registration_number,
                vehicle_type=entity.vehicle_type,
                capacity_kg=entity.capacity_kg,
                is_reefer=entity.is_reefer,
                status=entity.status,
            )
        )
        await self._session.flush()
        return entity

    async def get(self, vehicle_id: UUID) -> Vehicle | None:
        result = await self._session.execute(
            select(VehicleModel).where(VehicleModel.id == vehicle_id)
        )
        model = result.scalar_one_or_none()
        return to_vehicle_entity(model) if model else None

    async def list(self) -> list[Vehicle]:
        result = await self._session.execute(
            select(VehicleModel).order_by(VehicleModel.registration_number)
        )
        return [to_vehicle_entity(model) for model in result.scalars().all()]


class SqlAlchemyContainerRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, entity: ColdContainer) -> ColdContainer:
        self._session.add(
            ContainerModel(
                id=entity.container_id,
                asset_tag=entity.asset_tag,
                temperature_setpoint=entity.temperature_setpoint,
                min_temperature=entity.min_temperature,
                max_temperature=entity.max_temperature,
                status=entity.status,
                current_latitude=entity.current_latitude,
                current_longitude=entity.current_longitude,
                battery_level=entity.battery_level,
            )
        )
        await self._session.flush()
        return entity

    async def get(self, container_id: UUID) -> ColdContainer | None:
        result = await self._session.execute(
            select(ContainerModel).where(ContainerModel.id == container_id)
        )
        model = result.scalar_one_or_none()
        return to_container_entity(model) if model else None

    async def list(self) -> list[ColdContainer]:
        result = await self._session.execute(
            select(ContainerModel).order_by(ContainerModel.asset_tag)
        )
        return [to_container_entity(model) for model in result.scalars().all()]

    async def update(self, entity: ColdContainer) -> ColdContainer:
        result = await self._session.execute(
            select(ContainerModel).where(ContainerModel.id == entity.container_id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return entity
        model.current_latitude = entity.current_latitude
        model.current_longitude = entity.current_longitude
        model.battery_level = entity.battery_level
        model.status = entity.status
        await self._session.flush()
        return entity
