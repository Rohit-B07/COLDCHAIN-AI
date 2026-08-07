"""Notification service: aggregates cold-chain events into a feed.

There is no dedicated notification table. The feed is derived from the three
sources that already model cold-chain events - predictions, alerts and
shipments - reusing the existing repository read methods so no persistence
logic is duplicated:

- predictions -> ``prediction`` notifications (always unread)
- open/acknowledged alerts -> ``alert`` notifications (open = unread,
  acknowledged = read, resolved alerts are excluded)
- shipments -> ``shipment`` status notifications (always unread)

Notification ids are deterministic (namespace uuid5 over the source) so the
same source event always maps to the same notification id across requests.
"""

import builtins
from datetime import UTC, datetime
from typing import cast
from uuid import NAMESPACE_URL, uuid5

from app.domain.entities.intelligence import ColdAlert, Prediction
from app.domain.entities.shipment import Shipment
from app.domain.repositories import (
    AlertRepository,
    PredictionRepository,
    ShipmentRepository,
)
from app.schemas.notification import (
    NotificationItem,
    NotificationSeverityValue,
    NotificationTypeValue,
)

_NAMESPACE = NAMESPACE_URL

_RISK_TO_SEVERITY: dict[str, NotificationSeverityValue] = {
    "low": "info",
    "medium": "warning",
    "high": "critical",
    "critical": "critical",
}


def _severity_for_risk(risk_level: str) -> NotificationSeverityValue:
    return _RISK_TO_SEVERITY.get(risk_level, "info")


def _weather_message(explanations: dict) -> str:
    for rule in explanations.get("rules") or []:
        if rule.get("name") == "ambient_temperature_delta":
            detail = rule.get("detail")
            if detail:
                return str(detail)
    return "Temperature-excursion risk predicted for this shipment"


def _prediction_item(prediction: Prediction) -> NotificationItem:
    created_at = prediction.created_at or datetime.now(UTC)
    return NotificationItem(
        id=uuid5(
            _NAMESPACE, f"coldchain:notification:prediction:{prediction.prediction_id}"
        ),
        type=cast(NotificationTypeValue, "prediction"),
        title=f"Excursion risk: {prediction.risk_level}",
        message=_weather_message(prediction.explanations),
        severity=_severity_for_risk(prediction.risk_level),
        created_at=created_at,
        shipment_id=prediction.shipment_id,
        prediction_id=prediction.prediction_id,
        read=False,
    )


def _alert_item(alert: ColdAlert, *, read: bool) -> NotificationItem:
    created_at = alert.created_at or datetime.now(UTC)
    return NotificationItem(
        id=uuid5(_NAMESPACE, f"coldchain:notification:alert:{alert.alert_id}"),
        type=cast(NotificationTypeValue, "alert"),
        title=alert.alert_type.replace("_", " ").capitalize(),
        message=alert.message,
        severity=cast(NotificationSeverityValue, alert.severity),
        created_at=created_at,
        shipment_id=alert.shipment_id,
        read=read,
    )


def _shipment_item(shipment: Shipment) -> NotificationItem:
    timestamp = shipment.delivered_at or shipment.dispatched_at or shipment.created_at
    return NotificationItem(
        id=uuid5(_NAMESPACE, f"coldchain:notification:shipment:{shipment.shipment_id}"),
        type=cast(NotificationTypeValue, "shipment"),
        title=f"Shipment {shipment.tracking_code}",
        message=(
            f"Shipment {shipment.tracking_code} is now "
            f"{shipment.status.value.replace('_', ' ')}"
        ),
        severity=cast(NotificationSeverityValue, "info"),
        created_at=timestamp or datetime.now(UTC),
        shipment_id=shipment.shipment_id,
        read=False,
    )


class NotificationService:
    """Aggregate recent predictions, alerts and shipments into a feed."""

    def __init__(
        self,
        prediction_repo: PredictionRepository,
        alert_repo: AlertRepository,
        shipment_repo: ShipmentRepository,
    ) -> None:
        self._predictions = prediction_repo
        self._alerts = alert_repo
        self._shipments = shipment_repo

    async def counts(self) -> tuple[int, int]:
        """Return ``(total, unread_count)`` for the unfiltered feed."""
        prediction_total = await self._predictions.count()
        open_total = await self._alerts.count(status="open")
        acknowledged_total = await self._alerts.count(status="acknowledged")
        shipment_total = await self._shipments.count()
        total = prediction_total + open_total + acknowledged_total + shipment_total
        unread_count = prediction_total + open_total + shipment_total
        return total, unread_count

    async def list(
        self,
        *,
        page: int = 1,
        size: int = 20,
        unread_only: bool = False,
    ) -> tuple[builtins.list[NotificationItem], int, int, int]:
        """Return ``(page_items, total, pages, unread_count)`` newest first.

        ``total`` honours the ``unread_only`` filter; ``unread_count`` is always
        the number of unread notifications in the unfiltered feed.
        """
        offset = (page - 1) * size
        needed = offset + size

        total, unread_count = await self.counts()

        predictions = await self._predictions.list_paginated(limit=needed)
        open_alerts = await self._alerts.list_paginated(status="open", limit=needed)
        acknowledged_alerts = await self._alerts.list_paginated(
            status="acknowledged", limit=needed
        )
        shipments = await self._shipments.list_paginated(limit=needed)

        items: builtins.list[NotificationItem] = [
            _prediction_item(p) for p in predictions
        ]
        items.extend(_alert_item(a, read=False) for a in open_alerts)
        items.extend(_alert_item(a, read=True) for a in acknowledged_alerts)
        items.extend(_shipment_item(s) for s in shipments)
        items.sort(key=lambda item: item.created_at, reverse=True)

        if unread_only:
            total = unread_count
            page_items = [item for item in items if not item.read][
                offset : offset + size
            ]
        else:
            page_items = items[offset : offset + size]

        pages = (total + size - 1) // size if total else 0
        return page_items, total, pages, unread_count
