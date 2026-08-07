"""Analytics service: operational KPIs aggregated from live platform data.

All figures are derived from existing repositories - no mock data and no
hand-written SQL. Shipment status counts are computed from the single ``list``
read already offered by the shipment repository; prediction risk-level counts
reuse the filtered ``count``; notification totals reuse ``NotificationService``
so the notification-center and analytics numbers can never drift apart.
"""

from datetime import UTC, datetime

from app.domain.repositories import (
    AlertRepository,
    PredictionRepository,
    ShipmentRepository,
)
from app.schemas.analytics import (
    AlertStats,
    AnalyticsDashboardResponse,
    NotificationStats,
    PredictionStats,
    ShipmentStats,
    TemperatureStats,
)
from app.services.notification_service import NotificationService

ACTIVE_STATUSES = frozenset({"predicted", "dispatched", "in_transit"})
DELIVERED_STATUS = "delivered"

# Bounded window for temperature aggregation; the KPI is a summary over recent
# predictions rather than a whole-table scan.
_TEMPERATURE_WINDOW = 5000


class AnalyticsService:
    """Aggregate operational KPIs for the analytics dashboard."""

    def __init__(
        self,
        shipment_repo: ShipmentRepository,
        prediction_repo: PredictionRepository,
        alert_repo: AlertRepository,
        notification_service: NotificationService,
    ) -> None:
        self._shipments = shipment_repo
        self._predictions = prediction_repo
        self._alerts = alert_repo
        self._notifications = notification_service

    async def get_dashboard(self) -> AnalyticsDashboardResponse:
        shipments = await self._shipments.list()
        shipment_stats = self._shipment_stats(shipments)

        prediction_stats = PredictionStats(
            total=await self._predictions.count(),
            critical=await self._predictions.count(risk_level="critical"),
            high=await self._predictions.count(risk_level="high"),
            medium=await self._predictions.count(risk_level="medium"),
            low=await self._predictions.count(risk_level="low"),
        )

        temperature_stats = await self._temperature_stats()

        alert_stats = AlertStats(
            open=await self._alerts.count(status="open"),
            resolved=await self._alerts.count(status="resolved"),
        )

        notification_total, notification_unread = await self._notifications.counts()
        notification_stats = NotificationStats(
            unread=notification_unread,
            total=notification_total,
        )

        return AnalyticsDashboardResponse(
            shipments=shipment_stats,
            predictions=prediction_stats,
            alerts=alert_stats,
            notifications=notification_stats,
            temperature=temperature_stats,
        )

    def _shipment_stats(self, shipments: list) -> ShipmentStats:
        now = datetime.now(UTC)
        active = 0
        completed = 0
        delayed = 0
        for shipment in shipments:
            status = shipment.status.value
            if status in ACTIVE_STATUSES:
                active += 1
                if (
                    shipment.estimated_delivery_at is not None
                    and shipment.estimated_delivery_at < now
                ):
                    delayed += 1
            elif status == DELIVERED_STATUS:
                completed += 1
        return ShipmentStats(
            total=len(shipments),
            active=active,
            completed=completed,
            delayed=delayed,
        )

    async def _temperature_stats(self) -> TemperatureStats:
        predictions = await self._predictions.list_paginated(limit=_TEMPERATURE_WINDOW)
        if not predictions:
            return TemperatureStats(average=0.0, maximum=0.0, minimum=0.0)
        midpoints = [
            (p.expected_min_temp + p.expected_max_temp) / 2 for p in predictions
        ]
        return TemperatureStats(
            average=round(sum(midpoints) / len(midpoints), 2),
            maximum=max(p.expected_max_temp for p in predictions),
            minimum=min(p.expected_min_temp for p in predictions),
        )
