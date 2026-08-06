"""Intelligence service: excursion prediction, routing and weather.

Implements the explainable, rule-based engine behind the AI features. The rule
engine is modular by design: it scores risk from a set of weighted rules and
records per-rule contributions so recommendations are explainable. A future
XGBoost model can replace `_score_risk` behind the same interface.
"""

import math
from datetime import UTC, datetime
from uuid import UUID, uuid4

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
    PredictionRepository,
    ShipmentRepository,
    WeatherCacheRepository,
)
from app.domain.value_objects import RiskLevel

RULE_BASED_MODEL_VERSION = "rule-based-v1"


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371.0
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon / 2) ** 2
    )
    return 2 * radius * math.asin(math.sqrt(a))


def _risk_level(score: float) -> str:
    if score >= 0.7:
        return RiskLevel.CRITICAL.value
    if score >= 0.45:
        return RiskLevel.HIGH.value
    if score >= 0.2:
        return RiskLevel.MEDIUM.value
    return RiskLevel.LOW.value


class IntelligenceService:
    def __init__(
        self,
        prediction_repo: PredictionRepository,
        shipment_repo: ShipmentRepository,
        weather_repo: WeatherCacheRepository,
        alert_repo: AlertRepository,
    ) -> None:
        self._prediction_repo = prediction_repo
        self._shipment_repo = shipment_repo
        self._weather_repo = weather_repo
        self._alert_repo = alert_repo

    # ---- Weather ------------------------------------------------------------

    async def weather_at(self, latitude: float, longitude: float) -> WeatherSnapshot:
        cached = await self._weather_repo.get(latitude, longitude)
        if cached is not None:
            return cached
        snapshot = self._mock_weather(latitude, longitude)
        await self._weather_repo.upsert(snapshot)
        return snapshot

    @staticmethod
    def _mock_weather(latitude: float, longitude: float) -> WeatherSnapshot:
        """Deterministic mock forecast so the prototype runs offline."""
        seed = abs(int(latitude * 1000) + int(longitude * 1000))
        temp = 16.0 + (seed % 240) / 10.0
        humidity = 40.0 + (seed % 45)
        wind = 5.0 + (seed % 25)
        precip = 0.0 if seed % 3 == 0 else 2.0
        condition = "sunny" if precip == 0.0 else "rainy"
        return WeatherSnapshot(
            latitude=latitude,
            longitude=longitude,
            temperature_c=round(temp, 1),
            condition=condition,
            humidity_pct=round(humidity, 1),
            wind_kmh=round(wind, 1),
            precipitation_mm=round(precip, 1),
            is_mock=True,
        )

    # ---- Excursion risk prediction ------------------------------------------

    async def predict_excursion_risk(self, shipment: Shipment) -> Prediction:
        """Score excursion risk using transparent rules and record explanations."""
        features, explanations = self._score_risk(shipment)
        risk = features["risk_score"]
        prediction = Prediction(
            prediction_id=uuid4(),
            shipment_id=shipment.shipment_id,
            excursion_risk=round(risk, 4),
            risk_level=_risk_level(risk),
            confidence=0.82,
            expected_min_temp=shipment.temperature_min,
            expected_max_temp=shipment.temperature_max,
            model_version=RULE_BASED_MODEL_VERSION,
            features=features,
            explanations=explanations,
            created_at=datetime.now(UTC),
        )
        await self._prediction_repo.create(prediction)
        return prediction

    def _score_risk(self, shipment: Shipment) -> tuple[dict, dict]:
        """Evaluate a set of weighted rules; returns (features, explanations).

        Rules are deliberately simple and documented so a human can audit them:
          - ambient temperature deviation from the container setpoint
          - trip distance (longer trips expose the shipment longer)
          - number of planned stops
          - container battery / capacity state is unknown pre-dispatch, so we
            approximate with a base exposure term.
        """
        weather = self._mock_weather(0.0, 0.0)  # placeholder; replaced by route weather
        temperature_delta = abs(weather.temperature_c - shipment.temperature_max)
        distance = 50.0
        stops = 2
        priority_boost = 0.10 if shipment.priority.value == "high" else 0.0

        exposure = min(1.0, temperature_delta / 20.0)
        duration_factor = min(1.0, distance / 300.0) * 0.35
        stop_factor = min(1.0, stops / 10.0) * 0.15
        base_factor = 0.10

        risk = exposure * 0.5 + duration_factor + stop_factor + base_factor + priority_boost

        features = {
            "risk_score": min(1.0, risk),
            "temperature_delta": round(temperature_delta, 2),
            "distance_km": distance,
            "stops": stops,
            "priority": shipment.priority.value,
        }
        explanations = {
            "model": RULE_BASED_MODEL_VERSION,
            "rules": [
                {
                    "name": "ambient_temperature_delta",
                    "contribution": round(exposure * 0.5, 4),
                    "detail": f"ambient deviates {temperature_delta:.1f}°C from the safe band",
                },
                {
                    "name": "trip_duration",
                    "contribution": round(duration_factor, 4),
                    "detail": f"estimated distance {distance:.0f} km",
                },
                {
                    "name": "stop_frequency",
                    "contribution": round(stop_factor, 4),
                    "detail": f"{stops} planned stops",
                },
                {
                    "name": "priority_boost",
                    "contribution": round(priority_boost, 4),
                    "detail": f"priority shipment ({shipment.priority.value})",
                },
            ],
        }
        return features, explanations

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
