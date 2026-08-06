"""Shipment endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.deps.container import get_shipment_service
from app.api.deps.rbac import require_permissions
from app.domain.entities.shipment import Shipment as ShipmentEntity
from app.domain.permissions import Permission
from app.schemas.common import ApiResponse, Page
from app.schemas.shipment import (
    DispatchRequest,
    ShipmentCreate,
    ShipmentQueryParams,
    ShipmentRead,
    ShipmentUpdate,
)
from app.services.shipment_service import ShipmentService

router = APIRouter(prefix="/shipments", tags=["shipments"])

_ViewShipments = Depends(require_permissions(Permission.SHIPMENT_VIEW))
_CreateShipments = Depends(require_permissions(Permission.SHIPMENT_CREATE))
_ManageShipments = Depends(require_permissions(Permission.SHIPMENT_UPDATE))


def _to_read(s: ShipmentEntity) -> ShipmentRead:
    return ShipmentRead(
        id=s.shipment_id,
        tracking_code=s.tracking_code,
        vaccine_name=s.vaccine_name,
        dose_count=s.dose_count,
        priority=s.priority,
        temperature_min=s.temperature_min,
        temperature_max=s.temperature_max,
        warehouse_id=s.warehouse_id,
        destination_id=s.destination_id,
        container_id=s.container_id,
        driver_id=s.driver_id,
        status=s.status,
        dispatched_at=s.dispatched_at,
        delivered_at=s.delivered_at,
        estimated_delivery_at=s.estimated_delivery_at,
        created_at=s.created_at,
        is_deleted=s.is_deleted,
        deleted_at=s.deleted_at,
    )


@router.get(
    "",
    response_model=ApiResponse[Page[ShipmentRead]],
    summary="List shipments (paginated and filtered)",
    dependencies=[_ViewShipments],
)
async def list_shipments(
    params: Annotated[ShipmentQueryParams, Query()],
    service: Annotated[ShipmentService, Depends(get_shipment_service)],
) -> ApiResponse[Page[ShipmentRead]]:
    items, total = await service.list(
        search=params.search,
        status=params.status.value if params.status else None,
        priority=params.priority.value if params.priority else None,
        page=params.page,
        size=params.size,
    )
    pages = (total + params.size - 1) // params.size if total else 0
    return ApiResponse(
        data=Page[ShipmentRead](
            items=[_to_read(s) for s in items],
            total=total,
            page=params.page,
            size=params.size,
            pages=pages,
        )
    )


@router.post(
    "",
    response_model=ApiResponse[ShipmentRead],
    status_code=201,
    summary="Create a shipment",
    dependencies=[_CreateShipments],
)
async def create_shipment(
    payload: ShipmentCreate,
    service: Annotated[ShipmentService, Depends(get_shipment_service)],
) -> ApiResponse[ShipmentRead]:
    saved = await service.create(payload)
    return ApiResponse(data=_to_read(saved))


@router.get(
    "/{shipment_id}",
    response_model=ApiResponse[ShipmentRead],
    summary="Get a shipment",
    dependencies=[_ViewShipments],
)
async def get_shipment(
    shipment_id: UUID,
    service: Annotated[ShipmentService, Depends(get_shipment_service)],
) -> ApiResponse[ShipmentRead]:
    shipment = await service.get(shipment_id)
    return ApiResponse(data=_to_read(shipment))


@router.patch(
    "/{shipment_id}",
    response_model=ApiResponse[ShipmentRead],
    summary="Update a shipment",
    dependencies=[_ManageShipments],
)
async def update_shipment(
    shipment_id: UUID,
    payload: ShipmentUpdate,
    service: Annotated[ShipmentService, Depends(get_shipment_service)],
) -> ApiResponse[ShipmentRead]:
    shipment = await service.update(shipment_id, payload)
    return ApiResponse(data=_to_read(shipment))


@router.post(
    "/{shipment_id}/dispatch",
    response_model=ApiResponse[ShipmentRead],
    summary="Dispatch a shipment with container and driver",
    dependencies=[_ManageShipments],
)
async def dispatch_shipment(
    shipment_id: UUID,
    payload: DispatchRequest,
    service: Annotated[ShipmentService, Depends(get_shipment_service)],
) -> ApiResponse[ShipmentRead]:
    shipment = await service.dispatch(shipment_id, payload)
    return ApiResponse(data=_to_read(shipment))


@router.post(
    "/{shipment_id}/cancel",
    response_model=ApiResponse[ShipmentRead],
    summary="Cancel a shipment",
    dependencies=[_ManageShipments],
)
async def cancel_shipment(
    shipment_id: UUID,
    service: Annotated[ShipmentService, Depends(get_shipment_service)],
) -> ApiResponse[ShipmentRead]:
    shipment = await service.cancel(shipment_id)
    return ApiResponse(data=_to_read(shipment))


@router.delete(
    "/{shipment_id}",
    response_model=ApiResponse[ShipmentRead],
    summary="Soft-delete a shipment",
    dependencies=[_ManageShipments],
)
async def delete_shipment(
    shipment_id: UUID,
    service: Annotated[ShipmentService, Depends(get_shipment_service)],
) -> ApiResponse[ShipmentRead]:
    shipment = await service.delete(shipment_id)
    return ApiResponse(data=_to_read(shipment))
