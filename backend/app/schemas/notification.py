"""Notification DTOs for the aggregated cold-chain notification feed.

Notifications are derived on the fly from predictions, alerts and shipments
(there is no dedicated notification table), so these schemas describe the
read-only contract returned by ``GET /api/v1/notifications``.
"""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

NotificationTypeValue = Literal["prediction", "alert", "shipment", "system"]
NotificationSeverityValue = Literal["info", "warning", "critical"]


class NotificationItem(BaseModel):
    """A single item in the notification feed."""

    id: UUID
    type: NotificationTypeValue
    title: str
    message: str
    severity: NotificationSeverityValue
    created_at: datetime
    shipment_id: UUID | None = None
    prediction_id: UUID | None = None
    read: bool = False


class NotificationQueryParams(BaseModel):
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)
    unread_only: bool = False


class NotificationFeed(BaseModel):
    """Pagination envelope for the feed (mirrors ``Page``) plus unread count."""

    items: list[NotificationItem]
    total: int
    page: int
    size: int
    pages: int
    unread_count: int
