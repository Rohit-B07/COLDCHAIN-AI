"""Vehicle endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.deps.container import get_vehicle_service
from app.api.deps.rbac import require_permissions
from app.domain.entities.logistics import Vehicle
from app.domain.permissions import Permission
from app.schemas.common import ApiResponse, Page
from app.schemas.vehicle import (
    VehicleCreate,
    VehicleMaintenanceUpdate,
    VehicleQueryParams,
    VehicleRead,
    VehicleStatusUpdate,
    VehicleUpdate,
)
from app.services.vehicle_service import VehicleService

router = APIRouter(prefix="/vehicles", tags=["vehicles"])

_ViewVehicles = Depends(require_permissions(Permission.LOGISTICS_VIEW))
_ManageVehicles = Depends(require_permissions(Permission.LOGISTICS_MANAGE))


def _read(entity: Vehicle) -> VehicleRead:
    return VehicleRead(
        id=entity.vehicle_id,
        registration_number=entity.registration_number,
        vehicle_type=entity.vehicle_type,
        capacity_kg=entity.capacity_kg,
        is_reefer=entity.is_reefer,
        status=entity.status,
        maintenance_status=entity.maintenance_status,
        last_maintenance_at=entity.last_maintenance_at,
        next_maintenance_due_at=entity.next_maintenance_due_at,
        is_deleted=entity.is_deleted,
        created_at=entity.created_at,
    )


@router.get(
    "",
    response_model=ApiResponse[Page[VehicleRead]],
    summary="List vehicles (paginated and filtered)",
    dependencies=[_ViewVehicles],
)
async def list_vehicles(
    params: Annotated[VehicleQueryParams, Query()],
    service: Annotated[VehicleService, Depends(get_vehicle_service)],
) -> ApiResponse[Page[VehicleRead]]:
    items, total = await service.list(
        search=params.search,
        status=params.status,
        vehicle_type=params.vehicle_type,
        page=params.page,
        size=params.size,
    )
    pages = (total + params.size - 1) // params.size if total else 0
    return ApiResponse(
        data=Page[VehicleRead](
            items=[_read(vehicle) for vehicle in items],
            total=total,
            page=params.page,
            size=params.size,
            pages=pages,
        )
    )


@router.post(
    "",
    response_model=ApiResponse[VehicleRead],
    status_code=201,
    summary="Create a vehicle",
    dependencies=[_ManageVehicles],
)
async def create_vehicle(
    payload: VehicleCreate,
    service: Annotated[VehicleService, Depends(get_vehicle_service)],
) -> ApiResponse[VehicleRead]:
    entity = await service.create(payload)
    return ApiResponse(data=_read(entity))


@router.get(
    "/{vehicle_id}",
    response_model=ApiResponse[VehicleRead],
    summary="Get a vehicle by id",
    dependencies=[_ViewVehicles],
)
async def get_vehicle(
    vehicle_id: UUID,
    service: Annotated[VehicleService, Depends(get_vehicle_service)],
) -> ApiResponse[VehicleRead]:
    entity = await service.get(vehicle_id)
    return ApiResponse(data=_read(entity))


@router.patch(
    "/{vehicle_id}",
    response_model=ApiResponse[VehicleRead],
    summary="Update a vehicle's profile",
    dependencies=[_ManageVehicles],
)
async def update_vehicle(
    vehicle_id: UUID,
    payload: VehicleUpdate,
    service: Annotated[VehicleService, Depends(get_vehicle_service)],
) -> ApiResponse[VehicleRead]:
    entity = await service.update(vehicle_id, payload)
    return ApiResponse(data=_read(entity))


@router.patch(
    "/{vehicle_id}/status",
    response_model=ApiResponse[VehicleRead],
    summary="Update a vehicle's status",
    dependencies=[_ManageVehicles],
)
async def update_vehicle_status(
    vehicle_id: UUID,
    payload: VehicleStatusUpdate,
    service: Annotated[VehicleService, Depends(get_vehicle_service)],
) -> ApiResponse[VehicleRead]:
    entity = await service.change_status(vehicle_id, payload)
    return ApiResponse(data=_read(entity))


@router.patch(
    "/{vehicle_id}/maintenance",
    response_model=ApiResponse[VehicleRead],
    summary="Update a vehicle's maintenance status",
    dependencies=[_ManageVehicles],
)
async def update_vehicle_maintenance(
    vehicle_id: UUID,
    payload: VehicleMaintenanceUpdate,
    service: Annotated[VehicleService, Depends(get_vehicle_service)],
) -> ApiResponse[VehicleRead]:
    entity = await service.set_maintenance_status(vehicle_id, payload)
    return ApiResponse(data=_read(entity))


@router.delete(
    "/{vehicle_id}",
    response_model=ApiResponse[VehicleRead],
    summary="Soft-delete a vehicle",
    dependencies=[_ManageVehicles],
)
async def delete_vehicle(
    vehicle_id: UUID,
    service: Annotated[VehicleService, Depends(get_vehicle_service)],
) -> ApiResponse[VehicleRead]:
    entity = await service.delete(vehicle_id)
    return ApiResponse(data=_read(entity))
