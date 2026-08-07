"""Analytics DTOs for the operational insights dashboard."""

from pydantic import BaseModel


class ShipmentStats(BaseModel):
    total: int
    active: int
    completed: int
    delayed: int


class PredictionStats(BaseModel):
    total: int
    critical: int
    high: int
    medium: int
    low: int


class AlertStats(BaseModel):
    open: int
    resolved: int


class NotificationStats(BaseModel):
    unread: int
    total: int


class TemperatureStats(BaseModel):
    average: float
    maximum: float
    minimum: float


class AnalyticsDashboardResponse(BaseModel):
    """Aggregated operational KPIs for the analytics dashboard."""

    shipments: ShipmentStats
    predictions: PredictionStats
    alerts: AlertStats
    notifications: NotificationStats
    temperature: TemperatureStats
