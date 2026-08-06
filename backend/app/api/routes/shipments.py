"""Shipment endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.deps.container import get_shipment_service
from app.domain.entities.shipment import Shipment as ShipmentEntity
from app.schemas.common import ApiResponse
from app.schemas.shipment import DispatchRequest, ShipmentCreate, ShipmentRead
from app.services.shipment_service import ShipmentService

router = APIRouter(prefix="/shipments", tags=["shipments"])


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
    )


@router.get("", response_model=ApiResponse[list[ShipmentRead]], summary="List shipments")
async def list_shipments(
    service: Annotated[ShipmentService, Depends(get_shipment_service)],
) -> ApiResponse[list[ShipmentRead]]:
    shipments = await service.list()
    return ApiResponse(data=[_to_read(s) for s in shipments])


@router.post(
    "", response_model=ApiResponse[ShipmentRead], status_code=201, summary="Create a shipment"
)
async def create_shipment(
    payload: ShipmentCreate,
    service: Annotated[ShipmentService, Depends(get_shipment_service)],
) -> ApiResponse[ShipmentRead]:
    entity = ShipmentEntity.create(
        tracking_code=f"SHP-{payload.destination_id.hex[:8].upper()}-{abs(hash(payload.vaccine_name)) % 1000}",
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
    saved = await service.create(entity)
    return ApiResponse(data=_to_read(saved))


@router.get("/{shipment_id}", response_model=ApiResponse[ShipmentRead], summary="Get a shipment")
async def get_shipment(
    shipment_id: UUID,
    service: Annotated[ShipmentService, Depends(get_shipment_service)],
) -> ApiResponse[ShipmentRead]:
    shipment = await service.get(shipment_id)
    return ApiResponse(data=_to_read(shipment))


@router.post(
    "/{shipment_id}/dispatch",
    response_model=ApiResponse[ShipmentRead],
    summary="Dispatch a shipment with container and driver",
)
async def dispatch_shipment(
    shipment_id: UUID,
    payload: DispatchRequest,
    service: Annotated[ShipmentService, Depends(get_shipment_service)],
) -> ApiResponse[ShipmentRead]:
    shipment = await service.dispatch(
        shipment_id=shipment_id,
        container_id=payload.container_id,
        driver_id=payload.driver_id,
    )
    return ApiResponse(data=_to_read(shipment))