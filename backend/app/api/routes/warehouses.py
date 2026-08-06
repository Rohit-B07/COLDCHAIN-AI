"""Warehouse management endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.deps.container import get_warehouse_service
from app.api.deps.rbac import require_permissions
from app.domain.entities.facility import Warehouse
from app.domain.permissions import Permission
from app.schemas.common import ApiResponse, Page
from app.schemas.warehouse import (
    WarehouseCreate,
    WarehouseQueryParams,
    WarehouseRead,
    WarehouseUpdate,
)
from app.services.warehouse_service import WarehouseService

router = APIRouter(prefix="/warehouses", tags=["warehouses"])

_ViewWarehouses = Depends(require_permissions(Permission.FACILITY_VIEW))
_ManageWarehouses = Depends(require_permissions(Permission.FACILITY_MANAGE))


def _read(entity: Warehouse) -> WarehouseRead:
    return WarehouseRead(
        id=entity.warehouse_id,
        name=entity.name,
        code=entity.code,
        latitude=entity.latitude,
        longitude=entity.longitude,
        address=entity.address,
        capacity=entity.capacity,
        is_deleted=entity.is_deleted,
        created_at=entity.created_at,
    )


@router.get(
    "",
    response_model=ApiResponse[Page[WarehouseRead]],
    summary="List warehouses (paginated and filtered)",
    dependencies=[_ViewWarehouses],
)
async def list_warehouses(
    params: Annotated[WarehouseQueryParams, Query()],
    service: Annotated[WarehouseService, Depends(get_warehouse_service)],
) -> ApiResponse[Page[WarehouseRead]]:
    items, total = await service.list(
        search=params.search,
        capacity_min=params.capacity_min,
        capacity_max=params.capacity_max,
        page=params.page,
        size=params.size,
    )
    pages = (total + params.size - 1) // params.size if total else 0
    return ApiResponse(
        data=Page[WarehouseRead](
            items=[_read(warehouse) for warehouse in items],
            total=total,
            page=params.page,
            size=params.size,
            pages=pages,
        )
    )


@router.post(
    "",
    response_model=ApiResponse[WarehouseRead],
    status_code=201,
    summary="Create a warehouse",
    dependencies=[_ManageWarehouses],
)
async def create_warehouse(
    payload: WarehouseCreate,
    service: Annotated[WarehouseService, Depends(get_warehouse_service)],
) -> ApiResponse[WarehouseRead]:
    entity = await service.create(payload)
    return ApiResponse(data=_read(entity))


@router.get(
    "/{warehouse_id}",
    response_model=ApiResponse[WarehouseRead],
    summary="Get a warehouse by id",
    dependencies=[_ViewWarehouses],
)
async def get_warehouse(
    warehouse_id: UUID,
    service: Annotated[WarehouseService, Depends(get_warehouse_service)],
) -> ApiResponse[WarehouseRead]:
    entity = await service.get(warehouse_id)
    return ApiResponse(data=_read(entity))


@router.patch(
    "/{warehouse_id}",
    response_model=ApiResponse[WarehouseRead],
    summary="Update a warehouse",
    dependencies=[_ManageWarehouses],
)
async def update_warehouse(
    warehouse_id: UUID,
    payload: WarehouseUpdate,
    service: Annotated[WarehouseService, Depends(get_warehouse_service)],
) -> ApiResponse[WarehouseRead]:
    entity = await service.update(warehouse_id, payload)
    return ApiResponse(data=_read(entity))


@router.delete(
    "/{warehouse_id}",
    response_model=ApiResponse[WarehouseRead],
    summary="Soft-delete a warehouse",
    dependencies=[_ManageWarehouses],
)
async def delete_warehouse(
    warehouse_id: UUID,
    service: Annotated[WarehouseService, Depends(get_warehouse_service)],
) -> ApiResponse[WarehouseRead]:
    entity = await service.delete(warehouse_id)
    return ApiResponse(data=_read(entity))
