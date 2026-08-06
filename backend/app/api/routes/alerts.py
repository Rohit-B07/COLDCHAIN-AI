"""Alert endpoints: CRUD, acknowledgement, resolution and history."""

from typing import Annotated, cast
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.deps.auth import CurrentUser
from app.api.deps.container import get_alert_service
from app.api.deps.rbac import require_permissions
from app.domain.entities.intelligence import ColdAlert
from app.domain.permissions import Permission
from app.schemas.alert import (
    AlertCreate,
    AlertQueryParams,
    AlertRead,
    AlertSeverityValue,
    AlertStatusValue,
    AlertUpdate,
)
from app.schemas.common import ApiResponse, Page
from app.services.alert_service import AlertService

router = APIRouter(prefix="/alerts", tags=["alerts"])

_ViewAlerts = Depends(require_permissions(Permission.ALERT_VIEW))
_ManageAlerts = Depends(require_permissions(Permission.ALERT_MANAGE))
_AcknowledgeAlerts = Depends(require_permissions(Permission.ALERT_ACKNOWLEDGE))


def _read(alert: ColdAlert) -> AlertRead:
    return AlertRead(
        id=alert.alert_id,
        shipment_id=alert.shipment_id,
        container_id=alert.container_id,
        severity=cast(AlertSeverityValue, alert.severity),
        alert_type=alert.alert_type,
        message=alert.message,
        status=cast(AlertStatusValue, alert.status),
        acknowledged_by=alert.acknowledged_by,
        acknowledged_at=alert.acknowledged_at,
        created_at=alert.created_at,
    )


@router.get(
    "",
    response_model=ApiResponse[Page[AlertRead]],
    summary="List alerts (paginated and filtered)",
    dependencies=[_ViewAlerts],
)
async def list_alerts(
    params: Annotated[AlertQueryParams, Query()],
    service: Annotated[AlertService, Depends(get_alert_service)],
) -> ApiResponse[Page[AlertRead]]:
    items, total = await service.list(
        shipment_id=params.shipment_id,
        container_id=params.container_id,
        severity=params.severity,
        status=params.status,
        page=params.page,
        size=params.size,
    )
    pages = (total + params.size - 1) // params.size if total else 0
    return ApiResponse(
        data=Page[AlertRead](
            items=[_read(alert) for alert in items],
            total=total,
            page=params.page,
            size=params.size,
            pages=pages,
        )
    )


@router.post(
    "",
    response_model=ApiResponse[AlertRead],
    status_code=201,
    summary="Raise a cold-chain alert",
    dependencies=[_ManageAlerts],
)
async def create_alert(
    payload: AlertCreate,
    service: Annotated[AlertService, Depends(get_alert_service)],
) -> ApiResponse[AlertRead]:
    entity = await service.create(payload)
    return ApiResponse(data=_read(entity))


@router.get(
    "/{alert_id}",
    response_model=ApiResponse[AlertRead],
    summary="Get an alert by id",
    dependencies=[_ViewAlerts],
)
async def get_alert(
    alert_id: UUID,
    service: Annotated[AlertService, Depends(get_alert_service)],
) -> ApiResponse[AlertRead]:
    entity = await service.get(alert_id)
    return ApiResponse(data=_read(entity))


@router.patch(
    "/{alert_id}",
    response_model=ApiResponse[AlertRead],
    summary="Update an alert's severity, type or message",
    dependencies=[_ManageAlerts],
)
async def update_alert(
    alert_id: UUID,
    payload: AlertUpdate,
    service: Annotated[AlertService, Depends(get_alert_service)],
) -> ApiResponse[AlertRead]:
    entity = await service.update(alert_id, payload)
    return ApiResponse(data=_read(entity))


@router.post(
    "/{alert_id}/acknowledge",
    response_model=ApiResponse[AlertRead],
    summary="Acknowledge an open alert",
    dependencies=[_AcknowledgeAlerts],
)
async def acknowledge_alert(
    alert_id: UUID,
    user: CurrentUser,
    service: Annotated[AlertService, Depends(get_alert_service)],
) -> ApiResponse[AlertRead]:
    entity = await service.acknowledge(alert_id, user.user_id)
    return ApiResponse(data=_read(entity))


@router.post(
    "/{alert_id}/resolve",
    response_model=ApiResponse[AlertRead],
    summary="Resolve an open or acknowledged alert",
    dependencies=[_ManageAlerts],
)
async def resolve_alert(
    alert_id: UUID,
    service: Annotated[AlertService, Depends(get_alert_service)],
) -> ApiResponse[AlertRead]:
    entity = await service.resolve(alert_id)
    return ApiResponse(data=_read(entity))


@router.delete(
    "/{alert_id}",
    response_model=ApiResponse[AlertRead],
    summary="Delete an alert",
    dependencies=[_ManageAlerts],
)
async def delete_alert(
    alert_id: UUID,
    service: Annotated[AlertService, Depends(get_alert_service)],
) -> ApiResponse[AlertRead]:
    entity = await service.delete(alert_id)
    return ApiResponse(data=_read(entity))


@router.get(
    "/shipments/{shipment_id}/history",
    response_model=ApiResponse[list[AlertRead]],
    summary="List alert history for a shipment",
    dependencies=[_ViewAlerts],
)
async def alert_history(
    shipment_id: UUID,
    service: Annotated[AlertService, Depends(get_alert_service)],
) -> ApiResponse[list[AlertRead]]:
    alerts = await service.history(shipment_id)
    return ApiResponse(data=[_read(alert) for alert in alerts])
