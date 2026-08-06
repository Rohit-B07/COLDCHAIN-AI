"""Logistics endpoints: drivers, vehicles and cold containers."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.deps.container import (
    get_container_repository,
    get_driver_repository,
    get_vehicle_repository,
)
from app.core.exceptions import NotFoundError
from app.domain.entities.logistics import (
    ColdContainer as ContainerEntity,
    Driver as DriverEntity,
    Vehicle as VehicleEntity,
)
from app.domain.repositories import (
    ContainerRepository,
    DriverRepository,
    VehicleRepository,
)
from app.schemas.common import ApiResponse
from app.schemas.logistics import (
    ContainerCreate,
    ContainerLocationUpdate,
    ContainerRead,
    DriverCreate,
    DriverRead,
    VehicleCreate,
    VehicleRead,
)

router = APIRouter(tags=["logistics"])

driver_router = APIRouter(prefix="/drivers")
vehicle_router = APIRouter(prefix="/vehicles")
container_router = APIRouter(prefix="/containers")


@driver_router.get("", response_model=ApiResponse[list[DriverRead]], summary="List drivers")
async def list_drivers(
    repo: Annotated[DriverRepository, Depends(get_driver_repository)],
) -> ApiResponse[list[DriverRead]]:
    drivers = await repo.list()
    return ApiResponse(
        data=[
            DriverRead(
                id=d.driver_id,
                name=d.name,
                phone=d.phone,
                license_number=d.license_number,
                status=d.status,
                vehicle_id=d.vehicle_id,
            )
            for d in drivers
        ]
    )


@driver_router.post("", response_model=ApiResponse[DriverRead], status_code=201, summary="Create a driver")
async def create_driver(
    payload: DriverCreate,
    repo: Annotated[DriverRepository, Depends(get_driver_repository)],
) -> ApiResponse[DriverRead]:
    entity = DriverEntity.create(
        name=payload.name,
        phone=payload.phone,
        license_number=payload.license_number,
        vehicle_id=payload.vehicle_id,
    )
    saved = await repo.create(entity)
    return ApiResponse(
        data=DriverRead(
            id=saved.driver_id,
            name=saved.name,
            phone=saved.phone,
            license_number=saved.license_number,
            status=saved.status,
            vehicle_id=saved.vehicle_id,
        )
    )


@vehicle_router.get("", response_model=ApiResponse[list[VehicleRead]], summary="List vehicles")
async def list_vehicles(
    repo: Annotated[VehicleRepository, Depends(get_vehicle_repository)],
) -> ApiResponse[list[VehicleRead]]:
    vehicles = await repo.list()
    return ApiResponse(
        data=[
            VehicleRead(
                id=v.vehicle_id,
                registration_number=v.registration_number,
                vehicle_type=v.vehicle_type,
                capacity_kg=v.capacity_kg,
                is_reefer=v.is_reefer,
                status=v.status,
            )
            for v in vehicles
        ]
    )


@vehicle_router.post("", response_model=ApiResponse[VehicleRead], status_code=201, summary="Create a vehicle")
async def create_vehicle(
    payload: VehicleCreate,
    repo: Annotated[VehicleRepository, Depends(get_vehicle_repository)],
) -> ApiResponse[VehicleRead]:
    entity = VehicleEntity.create(
        registration_number=payload.registration_number,
        vehicle_type=payload.vehicle_type,
        capacity_kg=payload.capacity_kg,
        is_reefer=payload.is_reefer,
    )
    saved = await repo.create(entity)
    return ApiResponse(
        data=VehicleRead(
            id=saved.vehicle_id,
            registration_number=saved.registration_number,
            vehicle_type=saved.vehicle_type,
            capacity_kg=saved.capacity_kg,
            is_reefer=saved.is_reefer,
            status=saved.status,
        )
    )


@container_router.get(
    "", response_model=ApiResponse[list[ContainerRead]], summary="List cold containers"
)
async def list_containers(
    repo: Annotated[ContainerRepository, Depends(get_container_repository)],
) -> ApiResponse[list[ContainerRead]]:
    containers = await repo.list()
    return ApiResponse(
        data=[
            ContainerRead(
                id=c.container_id,
                asset_tag=c.asset_tag,
                temperature_setpoint=c.temperature_setpoint,
                min_temperature=c.min_temperature,
                max_temperature=c.max_temperature,
                status=c.status,
                current_latitude=c.current_latitude,
                current_longitude=c.current_longitude,
                battery_level=c.battery_level,
            )
            for c in containers
        ]
    )


@container_router.post(
    "", response_model=ApiResponse[ContainerRead], status_code=201, summary="Create a cold container"
)
async def create_container(
    payload: ContainerCreate,
    repo: Annotated[ContainerRepository, Depends(get_container_repository)],
) -> ApiResponse[ContainerRead]:
    entity = ContainerEntity.create(
        asset_tag=payload.asset_tag,
        temperature_setpoint=payload.temperature_setpoint,
        min_temperature=payload.min_temperature,
        max_temperature=payload.max_temperature,
    )
    saved = await repo.create(entity)
    return ApiResponse(
        data=ContainerRead(
            id=saved.container_id,
            asset_tag=saved.asset_tag,
            temperature_setpoint=saved.temperature_setpoint,
            min_temperature=saved.min_temperature,
            max_temperature=saved.max_temperature,
            status=saved.status,
            current_latitude=saved.current_latitude,
            current_longitude=saved.current_longitude,
            battery_level=saved.battery_level,
        )
    )


@container_router.patch(
    "/{container_id}/location",
    response_model=ApiResponse[ContainerRead],
    summary="Update container geolocation",
)
async def update_container_location(
    container_id: UUID,
    payload: ContainerLocationUpdate,
    repo: Annotated[ContainerRepository, Depends(get_container_repository)],
) -> ApiResponse[ContainerRead]:
    container = await repo.get(container_id)
    if container is None:
        raise NotFoundError("Container not found")
    container.current_latitude = payload.latitude
    container.current_longitude = payload.longitude
    container.battery_level = payload.battery_level
    await repo.update(container)
    return ApiResponse(
        data=ContainerRead(
            id=container.container_id,
            asset_tag=container.asset_tag,
            temperature_setpoint=container.temperature_setpoint,
            min_temperature=container.min_temperature,
            max_temperature=container.max_temperature,
            status=container.status,
            current_latitude=container.current_latitude,
            current_longitude=container.current_longitude,
            battery_level=container.battery_level,
        )
    )
