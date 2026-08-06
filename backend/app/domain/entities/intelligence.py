"""Domain entities for routing, prediction, weather and alerts."""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID


@dataclass
class WarmRoute:
    """A computed delivery route with a safety score."""

    route_id: UUID
    shipment_id: UUID
    distance_km: float
    duration_minutes: int
    stops: list = field(default_factory=list)
    polyline: str = ""
    weather_factor: float = 1.0
    safety_score: float = 0.0
    is_selected: bool = False


@dataclass
class Prediction:
    """Predicted temperature-excursion risk for a shipment."""

    prediction_id: UUID
    shipment_id: UUID
    excursion_risk: float
    risk_level: str
    confidence: float
    expected_min_temp: float
    expected_max_temp: float
    model_version: str
    features: dict = field(default_factory=dict)
    explanations: dict = field(default_factory=dict)
    created_at: datetime | None = None


@dataclass
class WeatherSnapshot:
    """A weather snapshot at a location."""

    latitude: float
    longitude: float
    temperature_c: float
    condition: str
    humidity_pct: float
    wind_kmh: float
    precipitation_mm: float
    is_mock: bool


@dataclass
class ColdAlert:
    """A cold-chain alert."""

    alert_id: UUID
    severity: str
    alert_type: str
    message: str
    shipment_id: UUID | None = None
    container_id: UUID | None = None
    status: str = "open"