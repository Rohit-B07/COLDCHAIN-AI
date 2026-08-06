"""Driver endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.deps.container import get_driver_service
from app.api.deps.rbac import require_permissions
from app.domain.entities.logistics import Driver
from app.domain.permissions import Permission
from app.schemas.common import ApiResponse, Page
from app.schemas.driver import (
    DriverAssign,
    DriverCreate,
    DriverQueryParams,
    DriverRead,
    DriverStatusUpdate,
    DriverUpdate,
)
from app.services.driver_service import DriverService

router = APIRouter(prefix="/drivers", tags=["drivers"])

_ViewDrivers = Depends(require_permissions(Permission.LOGISTICS_VIEW))
_ManageDrivers = Depends(require_permissions(Permission.LOGISTICS_MANAGE))


def _read(entity: Driver) -> DriverRead:
    return DriverRead(
        id=entity.driver_id,
        name=entity.name,
        phone=entity.phone,
        license_number=entity.license_number,
        status=entity.status,
        vehicle_id=entity.vehicle_id,
        is_deleted=entity.is_deleted,
        created_at=entity.created_at,
    )


@router.get(
    "",
    response_model=ApiResponse[Page[DriverRead]],
    summary="List drivers (paginated and filtered)",
    dependencies=[_ViewDrivers],
)
async def list_drivers(
    params: Annotated[DriverQueryParams, Query()],
    service: Annotated[DriverService, Depends(get_driver_service)],
) -> ApiResponse[Page[DriverRead]]:
    items, total = await service.list(
        search=params.search,
        status=params.status,
        page=params.page,
        size=params.size,
    )
    pages = (total + params.size - 1) // params.size if total else 0
    return ApiResponse(
        data=Page[DriverRead](
            items=[_read(driver) for driver in items],
            total=total,
            page=params.page,
            size=params.size,
            pages=pages,
        )
    )


@router.post(
    "",
    response_model=ApiResponse[DriverRead],
    status_code=201,
    summary="Create a driver",
    dependencies=[_ManageDrivers],
)
async def create_driver(
    payload: DriverCreate,
    service: Annotated[DriverService, Depends(get_driver_service)],
) -> ApiResponse[DriverRead]:
    entity = await service.create(payload)
    return ApiResponse(data=_read(entity))


@router.get(
    "/{driver_id}",
    response_model=ApiResponse[DriverRead],
    summary="Get a driver by id",
    dependencies=[_ViewDrivers],
)
async def get_driver(
    driver_id: UUID,
    service: Annotated[DriverService, Depends(get_driver_service)],
) -> ApiResponse[DriverRead]:
    entity = await service.get(driver_id)
    return ApiResponse(data=_read(entity))


@router.patch(
    "/{driver_id}",
    response_model=ApiResponse[DriverRead],
    summary="Update a driver's profile",
    dependencies=[_ManageDrivers],
)
async def update_driver(
    driver_id: UUID,
    payload: DriverUpdate,
    service: Annotated[DriverService, Depends(get_driver_service)],
) -> ApiResponse[DriverRead]:
    entity = await service.update(driver_id, payload)
    return ApiResponse(data=_read(entity))


@router.patch(
    "/{driver_id}/status",
    response_model=ApiResponse[DriverRead],
    summary="Update a driver's status",
    dependencies=[_ManageDrivers],
)
async def update_driver_status(
    driver_id: UUID,
    payload: DriverStatusUpdate,
    service: Annotated[DriverService, Depends(get_driver_service)],
) -> ApiResponse[DriverRead]:
    entity = await service.change_status(driver_id, payload)
    return ApiResponse(data=_read(entity))


@router.post(
    "/{driver_id}/assign",
    response_model=ApiResponse[DriverRead],
    summary="Assign a driver to a vehicle",
    dependencies=[_ManageDrivers],
)
async def assign_driver(
    driver_id: UUID,
    payload: DriverAssign,
    service: Annotated[DriverService, Depends(get_driver_service)],
) -> ApiResponse[DriverRead]:
    entity = await service.assign_vehicle(driver_id, payload.vehicle_id)
    return ApiResponse(data=_read(entity))


@router.delete(
    "/{driver_id}/assign",
    response_model=ApiResponse[DriverRead],
    summary="Unassign a driver from its vehicle",
    dependencies=[_ManageDrivers],
)
async def unassign_driver(
    driver_id: UUID,
    service: Annotated[DriverService, Depends(get_driver_service)],
) -> ApiResponse[DriverRead]:
    entity = await service.unassign_vehicle(driver_id)
    return ApiResponse(data=_read(entity))


@router.delete(
    "/{driver_id}",
    response_model=ApiResponse[DriverRead],
    summary="Soft-delete a driver",
    dependencies=[_ManageDrivers],
)
async def delete_driver(
    driver_id: UUID,
    service: Annotated[DriverService, Depends(get_driver_service)],
) -> ApiResponse[DriverRead]:
    entity = await service.delete(driver_id)
    return ApiResponse(data=_read(entity))
