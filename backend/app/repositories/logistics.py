"""SQLAlchemy async repositories for logistics assets."""

import builtins
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
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
            select(DriverModel).where(
                DriverModel.id == driver_id,
                DriverModel.is_deleted.is_(False),
            )
        )
        model = result.scalar_one_or_none()
        return to_driver_entity(model) if model else None

    async def get_by_phone(self, phone: str) -> Driver | None:
        result = await self._session.execute(
            select(DriverModel).where(DriverModel.phone == phone.strip())
        )
        model = result.scalar_one_or_none()
        return to_driver_entity(model) if model else None

    async def get_by_license(self, license_number: str) -> Driver | None:
        result = await self._session.execute(
            select(DriverModel).where(
                DriverModel.license_number == license_number.strip().upper()
            )
        )
        model = result.scalar_one_or_none()
        return to_driver_entity(model) if model else None

    async def get_assigned_driver(self, vehicle_id: UUID) -> Driver | None:
        result = await self._session.execute(
            select(DriverModel).where(
                DriverModel.vehicle_id == vehicle_id,
                DriverModel.is_deleted.is_(False),
            )
        )
        model = result.scalar_one_or_none()
        return to_driver_entity(model) if model else None

    async def update(self, entity: Driver) -> Driver:
        model = await self._session.get(DriverModel, entity.driver_id)
        if model is None:
            raise NotFoundError("Driver not found")
        model.name = entity.name
        model.phone = entity.phone
        model.license_number = entity.license_number
        model.status = entity.status
        model.vehicle_id = entity.vehicle_id
        await self._session.flush()
        return entity

    async def list(self) -> builtins.list[Driver]:
        result = await self._session.execute(
            select(DriverModel)
            .where(DriverModel.is_deleted.is_(False))
            .order_by(DriverModel.name)
        )
        return [to_driver_entity(model) for model in result.scalars().all()]

    async def count(
        self,
        *,
        search: str | None = None,
        status: str | None = None,
    ) -> int:
        query = self._apply_filters(
            select(func.count(DriverModel.id)),
            search=search,
            status=status,
        ).where(DriverModel.is_deleted.is_(False))
        result = await self._session.execute(query)
        return int(result.scalar_one())

    async def list_paginated(
        self,
        *,
        search: str | None = None,
        status: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> builtins.list[Driver]:
        query = self._apply_filters(
            select(DriverModel),
            search=search,
            status=status,
        ).where(DriverModel.is_deleted.is_(False))
        query = query.order_by(DriverModel.name).offset(offset).limit(limit)
        result = await self._session.execute(query)
        return [to_driver_entity(model) for model in result.scalars().all()]

    async def soft_delete(self, driver_id: UUID) -> Driver | None:
        model = await self._session.get(DriverModel, driver_id)
        if model is None:
            return None
        model.is_deleted = True
        model.deleted_at = datetime.now(UTC)
        await self._session.flush()
        return to_driver_entity(model)

    def _apply_filters(
        self,
        query: Select,
        *,
        search: str | None,
        status: str | None,
    ) -> Select:
        if search:
            pattern = f"%{search.strip().lower()}%"
            query = query.where(
                or_(
                    DriverModel.name.ilike(pattern),
                    DriverModel.phone.ilike(pattern),
                    DriverModel.license_number.ilike(pattern),
                )
            )
        if status:
            query = query.where(DriverModel.status == status.strip().lower())
        return query


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
            select(VehicleModel).where(
                VehicleModel.id == vehicle_id,
                VehicleModel.is_deleted.is_(False),
            )
        )
        model = result.scalar_one_or_none()
        return to_vehicle_entity(model) if model else None

    async def get_by_registration(self, registration_number: str) -> Vehicle | None:
        result = await self._session.execute(
            select(VehicleModel).where(
                VehicleModel.registration_number
                == registration_number.strip().upper()
            )
        )
        model = result.scalar_one_or_none()
        return to_vehicle_entity(model) if model else None

    async def update(self, entity: Vehicle) -> Vehicle:
        model = await self._session.get(VehicleModel, entity.vehicle_id)
        if model is None:
            raise NotFoundError("Vehicle not found")
        model.registration_number = entity.registration_number
        model.vehicle_type = entity.vehicle_type
        model.capacity_kg = entity.capacity_kg
        model.is_reefer = entity.is_reefer
        model.status = entity.status
        model.maintenance_status = entity.maintenance_status
        model.last_maintenance_at = entity.last_maintenance_at
        model.next_maintenance_due_at = entity.next_maintenance_due_at
        await self._session.flush()
        return entity

    async def list(self) -> builtins.list[Vehicle]:
        result = await self._session.execute(
            select(VehicleModel)
            .where(VehicleModel.is_deleted.is_(False))
            .order_by(VehicleModel.registration_number)
        )
        return [to_vehicle_entity(model) for model in result.scalars().all()]

    async def count(
        self,
        *,
        search: str | None = None,
        status: str | None = None,
        vehicle_type: str | None = None,
    ) -> int:
        query = self._apply_filters(
            select(func.count(VehicleModel.id)),
            search=search,
            status=status,
            vehicle_type=vehicle_type,
        ).where(VehicleModel.is_deleted.is_(False))
        result = await self._session.execute(query)
        return int(result.scalar_one())

    async def list_paginated(
        self,
        *,
        search: str | None = None,
        status: str | None = None,
        vehicle_type: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> builtins.list[Vehicle]:
        query = self._apply_filters(
            select(VehicleModel),
            search=search,
            status=status,
            vehicle_type=vehicle_type,
        ).where(VehicleModel.is_deleted.is_(False))
        query = query.order_by(VehicleModel.registration_number).offset(offset).limit(limit)
        result = await self._session.execute(query)
        return [to_vehicle_entity(model) for model in result.scalars().all()]

    async def soft_delete(self, vehicle_id: UUID) -> Vehicle | None:
        model = await self._session.get(VehicleModel, vehicle_id)
        if model is None:
            return None
        model.is_deleted = True
        model.deleted_at = datetime.now(UTC)
        await self._session.flush()
        return to_vehicle_entity(model)

    def _apply_filters(
        self,
        query: Select,
        *,
        search: str | None,
        status: str | None,
        vehicle_type: str | None,
    ) -> Select:
        if search:
            pattern = f"%{search.strip().lower()}%"
            query = query.where(VehicleModel.registration_number.ilike(pattern))
        if status:
            query = query.where(VehicleModel.status == status.strip().lower())
        if vehicle_type:
            query = query.where(VehicleModel.vehicle_type == vehicle_type)
        return query


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
