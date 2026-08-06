"""Intelligence DTOs: predictions, routes, weather and alerts."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.value_objects import RiskLevel


class PredictionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    shipment_id: UUID
    excursion_risk: float
    risk_level: RiskLevel | str
    confidence: float
    expected_min_temp: float
    expected_max_temp: float
    model_version: str
    features: dict
    explanations: dict
    created_at: datetime | None = None


class RouteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    shipment_id: UUID
    distance_km: float
    duration_minutes: int
    stops: list
    polyline: str
    weather_factor: float
    safety_score: float
    is_selected: bool


class WeatherRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    latitude: float
    longitude: float
    temperature_c: float
    precipitation_mm: float
    wind_kmh: float
    humidity_pct: float
    condition: str
    is_mock: bool
    fetched_at: datetime | None = None


class AlertCreate(BaseModel):
    severity: str = Field(default="warning")
    alert_type: str = Field(min_length=1, max_length=64)
    message: str = Field(min_length=1)
    shipment_id: UUID | None = None
    container_id: UUID | None = None


class AlertRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    shipment_id: UUID | None
    container_id: UUID | None
    severity: str
    alert_type: str
    message: str
    status: str
    acknowledged_by: UUID | None
    acknowledged_at: datetime | None
    created_at: datetime | None = None


class RouteAlternatives(BaseModel):
    shipment_id: UUID
    selected: RouteRead
    alternatives: list[RouteRead] = Field(default_factory=list)
