"""Notification endpoints: aggregated cold-chain event feed."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps.container import get_notification_service
from app.api.deps.rbac import require_permissions
from app.domain.permissions import Permission
from app.schemas.common import ApiResponse
from app.schemas.notification import NotificationFeed, NotificationQueryParams
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["notifications"])

_ViewNotifications = Depends(require_permissions(Permission.ALERT_VIEW))


@router.get(
    "",
    response_model=ApiResponse[NotificationFeed],
    summary="List notifications (paginated, newest first)",
    dependencies=[_ViewNotifications],
)
async def list_notifications(
    params: Annotated[NotificationQueryParams, Query()],
    service: Annotated[NotificationService, Depends(get_notification_service)],
) -> ApiResponse[NotificationFeed]:
    items, total, pages, unread_count = await service.list(
        page=params.page,
        size=params.size,
        unread_only=params.unread_only,
    )
    return ApiResponse(
        data=NotificationFeed(
            items=items,
            total=total,
            page=params.page,
            size=params.size,
            pages=pages,
            unread_count=unread_count,
        )
    )
