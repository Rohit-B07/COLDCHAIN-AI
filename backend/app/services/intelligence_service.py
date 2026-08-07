"""Intelligence service: excursion prediction, routing and weather.

Implements the explainable, rule-based engine behind the AI features. The rule
engine is modular by design: it scores risk from a set of weighted rules and
records per-rule contributions so recommendations are explainable. A future
XGBoost model can replace the scoring function behind the same interface.
"""

import math
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.core.config import Settings, get_settings
from app.core.exceptions import NotFoundError
from app.domain.entities.intelligence import (
    ColdAlert,
    Prediction,
    WarmRoute,
    WeatherSnapshot,
)
from app.domain.entities.shipment import Shipment
from app.domain.repositories import (
    AlertRepository,
    ContainerRepository,
    PhCentreRepository,
    PredictionRepository,
    ShipmentRepository,
    WarehouseRepository,
)
from app.domain.value_objects import RiskLevel
from app.services.weather_service import WeatherService

RULE_BASED_MODEL_VERSION = "rule-based-v1"


@dataclass(frozen=True)
class PredictionRules:
    """Configurable weights and thresholds for the rule-based risk model."""

    temperature_weight: float = 0.50
    duration_weight: float = 0.35
    stop_weight: float = 0.15
    base_risk: float = 0.10
    priority_boost: float = 0.10
    max_exposure_degrees: float = 20.0
    max_distance_km: float = 300.0
    max_stops: int = 10
    default_distance_km: float = 50.0
    default_stops: int = 2
    confidence_live: float = 0.90
    confidence_mock: float = 0.60
    risk_high_threshold: float = 0.45
    risk_critical_threshold: float = 0.70
    risk_medium_threshold: float = 0.20

    @classmethod
    def from_settings(cls, settings: Settings) -> "PredictionRules":
        """Build rule weights from application configuration."""
        return cls(
            temperature_weight=settings.PREDICTION_TEMPERATURE_WEIGHT,
            duration_weight=settings.PREDICTION_DURATION_WEIGHT,
            stop_weight=settings.PREDICTION_STOP_WEIGHT,
            base_risk=settings.PREDICTION_BASE_RISK,
            priority_boost=settings.PREDICTION_PRIORITY_BOOST,
            max_exposure_degrees=settings.PREDICTION_MAX_EXPOSURE_DEGREES,
            max_distance_km=settings.PREDICTION_MAX_DISTANCE_KM,
            max_stops=settings.PREDICTION_MAX_STOPS,
            default_distance_km=settings.PREDICTION_DEFAULT_DISTANCE_KM,
            default_stops=settings.PREDICTION_DEFAULT_STOPS,
            confidence_live=settings.PREDICTION_CONFIDENCE_LIVE,
            confidence_mock=settings.PREDICTION_CONFIDENCE_MOCK,
        )


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371.0
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon / 2) ** 2
    )
    return 2 * radius * math.asin(math.sqrt(a))


def _risk_level(score: float, rules: PredictionRules) -> str:
    if score >= rules.risk_critical_threshold:
        return RiskLevel.CRITICAL.value
    if score >= rules.risk_high_threshold:
        return RiskLevel.HIGH.value
    if score >= rules.risk_medium_threshold:
        return RiskLevel.MEDIUM.value
    return RiskLevel.LOW.value


def score_excursion_risk(
    *,
    temperature_delta: float,
    distance_km: float,
    stops: int,
    priority: str,
    rules: PredictionRules,
) -> tuple[float, dict, dict]:
    """Score excursion risk from a set of weighted, explainable rules.

    Returns ``(risk, features, explanations)``. Risk is bounded to ``[0, 1]``;
    each rule records its individual contribution so the recommendation can be
    audited. ``temperature_delta`` is the ambient temperature's deviation from
    the shipment's safe band (0 when inside the band).
    """
    exposure = min(1.0, temperature_delta / rules.max_exposure_degrees)
    duration_factor = min(1.0, distance_km / rules.max_distance_km)
    stop_factor = min(1.0, stops / rules.max_stops)
    priority_boost = rules.priority_boost if priority == "high" else 0.0

    risk = (
        exposure * rules.temperature_weight
        + duration_factor * rules.duration_weight
        + stop_factor * rules.stop_weight
        + rules.base_risk
        + priority_boost
    )
    risk = min(1.0, risk)

    features = {
        "risk_score": round(risk, 4),
        "temperature_delta": round(temperature_delta, 2),
        "distance_km": round(distance_km, 2),
        "stops": stops,
        "priority": priority,
    }
    explanations = {
        "model": RULE_BASED_MODEL_VERSION,
        "rules": [
            {
                "name": "ambient_temperature_delta",
                "contribution": round(exposure * rules.temperature_weight, 4),
                "detail": f"ambient deviates {temperature_delta:.1f}°C from the safe band",
            },
            {
                "name": "trip_duration",
                "contribution": round(duration_factor * rules.duration_weight, 4),
                "detail": f"estimated distance {distance_km:.0f} km",
            },
            {
                "name": "stop_frequency",
                "contribution": round(stop_factor * rules.stop_weight, 4),
                "detail": f"{stops} planned stops",
            },
            {
                "name": "priority_boost",
                "contribution": round(priority_boost, 4),
                "detail": f"priority shipment ({priority})",
            },
        ],
    }
    return risk, features, explanations


class IntelligenceService:
    def __init__(
        self,
        prediction_repo: PredictionRepository,
        shipment_repo: ShipmentRepository,
        weather_service: WeatherService,
        alert_repo: AlertRepository,
        warehouse_repo: WarehouseRepository,
        phc_repo: PhCentreRepository,
        container_repo: ContainerRepository,
        settings: Settings | None = None,
        rules: PredictionRules | None = None,
    ) -> None:
        self._prediction_repo = prediction_repo
        self._shipment_repo = shipment_repo
        self._weather_service = weather_service
        self._alert_repo = alert_repo
        self._warehouses = warehouse_repo
        self._phcs = phc_repo
        self._containers = container_repo
        self._settings = settings or get_settings()
        self._rules = rules or PredictionRules.from_settings(self._settings)

    # ---- Weather ------------------------------------------------------------

    async def weather_at(self, latitude: float, longitude: float) -> WeatherSnapshot:
        return await self._weather_service.get_weather(latitude, longitude)

    # ---- Excursion risk prediction ------------------------------------------

    async def predict_excursion_risk(self, shipment: Shipment) -> Prediction:
        """Score excursion risk using transparent rules and record explanations.

        Uses real route geometry (warehouse → PHC coordinates) for the trip
        distance, weather at the destination, and the container's safe band
        when one is assigned. Confidence reflects the weather data source: live
        observations score higher than the deterministic mock fallback.
        """
        warehouse = await self._warehouses.get(shipment.warehouse_id)
        phc = await self._phcs.get(shipment.destination_id)
        if warehouse is not None and phc is not None:
            distance_km = _haversine_km(
                warehouse.latitude,
                warehouse.longitude,
                phc.latitude,
                phc.longitude,
            )
            weather = await self.weather_at(phc.latitude, phc.longitude)
        else:
            distance_km = self._rules.default_distance_km
            weather = await self.weather_at(0.0, 0.0)

        if shipment.container_id is not None:
            container = await self._containers.get(shipment.container_id)
            if container is not None:
                band_min = container.min_temperature
                band_max = container.max_temperature
            else:
                band_min, band_max = shipment.temperature_min, shipment.temperature_max
        else:
            band_min, band_max = shipment.temperature_min, shipment.temperature_max

        if weather.temperature_c < band_min:
            temperature_delta = band_min - weather.temperature_c
        elif weather.temperature_c > band_max:
            temperature_delta = weather.temperature_c - band_max
        else:
            temperature_delta = 0.0

        risk, features, explanations = score_excursion_risk(
            temperature_delta=temperature_delta,
            distance_km=distance_km,
            stops=self._rules.default_stops,
            priority=shipment.priority.value,
            rules=self._rules,
        )
        confidence = (
            self._rules.confidence_live
            if not weather.is_mock
            else self._rules.confidence_mock
        )

        prediction = Prediction(
            prediction_id=uuid4(),
            shipment_id=shipment.shipment_id,
            excursion_risk=round(risk, 4),
            risk_level=_risk_level(risk, self._rules),
            confidence=confidence,
            expected_min_temp=band_min,
            expected_max_temp=band_max,
            model_version=RULE_BASED_MODEL_VERSION,
            features=features,
            explanations=explanations,
            created_at=datetime.now(UTC),
        )
        await self._prediction_repo.create(prediction)
        return prediction

    # ---- Route optimisation ---------------------------------------------------

    async def plan_route(
        self, shipment: Shipment, origin: tuple[float, float], destination: tuple[float, float]
    ) -> WarmRoute:
        distance = _haversine_km(*origin, *destination)
        duration = int(distance / 45.0 * 60) + 15
        weather = await self.weather_at(*destination)
        weather_factor = 1.0 + (weather.precipitation_mm * 0.04) + (weather.wind_kmh * 0.002)
        safety = max(0.0, min(1.0, 1.0 - (weather_factor - 1.0) * 0.5))
        return WarmRoute(
            route_id=uuid4(),
            shipment_id=shipment.shipment_id,
            distance_km=round(distance, 2),
            duration_minutes=duration,
            stops=[{"type": "origin", "lat": origin[0], "lon": origin[1]}],
            polyline="",
            weather_factor=round(weather_factor, 4),
            safety_score=round(safety, 4),
            is_selected=True,
        )

    # ---- Alerts ---------------------------------------------------------------

    async def raise_alert(
        self,
        severity: str,
        alert_type: str,
        message: str,
        shipment_id: UUID | None = None,
        container_id: UUID | None = None,
    ) -> ColdAlert:
        alert = ColdAlert(
            alert_id=uuid4(),
            severity=severity,
            alert_type=alert_type,
            message=message,
            shipment_id=shipment_id,
            container_id=container_id,
        )
        return await self._alert_repo.create(alert)

    async def list_alerts(self, status: str | None = None) -> list[ColdAlert]:
        return await self._alert_repo.list(status=status)

    async def acknowledge_alert(self, alert_id: UUID, user_id: UUID) -> ColdAlert:
        alert = await self._alert_repo.acknowledge(alert_id, user_id)
        if alert is None:
            raise NotFoundError("Alert not found")
        return alert
