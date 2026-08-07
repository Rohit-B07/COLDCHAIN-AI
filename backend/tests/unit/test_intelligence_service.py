"""Unit tests for the explainable excursion-risk rule engine (no DB)."""

from datetime import UTC, datetime
from uuid import uuid4

from app.core.config import Settings
from app.domain.entities.intelligence import Prediction, WeatherSnapshot
from app.domain.entities.shipment import Shipment
from app.domain.repositories import PredictionRepository
from app.services.intelligence_service import (
    RULE_BASED_MODEL_VERSION,
    IntelligenceService,
    PredictionRules,
    _haversine_km,
    score_excursion_risk,
)

DEFAULT_RULES = PredictionRules()


class FakeWeatherService:
    def __init__(self, snapshot: WeatherSnapshot) -> None:
        self._snapshot = snapshot

    async def get_weather(self, latitude: float, longitude: float) -> WeatherSnapshot:
        return self._snapshot


class FakePredictionRepo(PredictionRepository):
    def __init__(self) -> None:
        self.created: list[Prediction] = []

    async def create(self, entity: Prediction) -> Prediction:
        self.created.append(entity)
        return entity


class _EmptyRepo:
    async def get(self, *_args, **_kwargs):
        return None

    async def create(self, entity, *_args, **_kwargs):
        return entity

    async def upsert(self, *_args, **_kwargs):
        return None


def _make_shipment(temperature_min: float = 2.0, temperature_max: float = 8.0) -> Shipment:
    return Shipment.create(
        tracking_code="SHP-ENGINE01",
        vaccine_name="BCG Vaccine",
        dose_count=100,
        warehouse_id=uuid4(),
        destination_id=uuid4(),
        priority="high",
        temperature_min=temperature_min,
        temperature_max=temperature_max,
    )


def _snapshot(temperature_c: float, *, is_mock: bool = False) -> WeatherSnapshot:
    return WeatherSnapshot(
        latitude=18.9,
        longitude=72.8,
        temperature_c=temperature_c,
        condition="sunny",
        humidity_pct=50.0,
        wind_kmh=5.0,
        precipitation_mm=0.0,
        is_mock=is_mock,
        fetched_at=datetime.now(UTC),
    )


def _service(snapshot: WeatherSnapshot) -> IntelligenceService:
    return IntelligenceService(
        prediction_repo=FakePredictionRepo(),
        shipment_repo=_EmptyRepo(),  # type: ignore[arg-type]
        weather_service=FakeWeatherService(snapshot),  # type: ignore[arg-type]
        alert_repo=_EmptyRepo(),  # type: ignore[arg-type]
        warehouse_repo=_EmptyRepo(),  # type: ignore[arg-type]
        phc_repo=_EmptyRepo(),  # type: ignore[arg-type]
        container_repo=_EmptyRepo(),  # type: ignore[arg-type]
        rules=DEFAULT_RULES,
    )


class TestScoreExcursionRisk:
    def test_zero_delta_inside_band_is_low_risk(self) -> None:
        risk, features, explanations = score_excursion_risk(
            temperature_delta=0.0,
            distance_km=50.0,
            stops=2,
            priority="low",
            rules=DEFAULT_RULES,
        )
        assert risk <= DEFAULT_RULES.risk_medium_threshold
        assert features["risk_score"] == round(risk, 4)
        assert any(r["name"] == "ambient_temperature_delta" for r in explanations["rules"])

    def test_large_delta_yields_high_risk(self) -> None:
        risk, _, _ = score_excursion_risk(
            temperature_delta=25.0,
            distance_km=300.0,
            stops=8,
            priority="high",
            rules=DEFAULT_RULES,
        )
        assert risk >= DEFAULT_RULES.risk_high_threshold
        assert risk <= 1.0

    def test_risk_is_bounded(self) -> None:
        risk, _, _ = score_excursion_risk(
            temperature_delta=500.0,
            distance_km=5000.0,
            stops=100,
            priority="high",
            rules=DEFAULT_RULES,
        )
        assert 0.0 <= risk <= 1.0

    def test_high_priority_boosts_risk(self) -> None:
        base, _, _ = score_excursion_risk(
            temperature_delta=5.0, distance_km=100.0, stops=2, priority="low", rules=DEFAULT_RULES
        )
        boosted, _, _ = score_excursion_risk(
            temperature_delta=5.0,
            distance_km=100.0,
            stops=2,
            priority="high",
            rules=DEFAULT_RULES,
        )
        assert boosted > base

    def test_configurable_weights_are_respected(self) -> None:
        rules = PredictionRules(
            temperature_weight=1.0,
            duration_weight=0.0,
            stop_weight=0.0,
            base_risk=0.0,
            priority_boost=0.0,
        )
        risky, _, _ = score_excursion_risk(
            temperature_delta=20.0, distance_km=0.0, stops=0, priority="low", rules=rules
        )
        safe, _, _ = score_excursion_risk(
            temperature_delta=0.0, distance_km=0.0, stops=0, priority="low", rules=rules
        )
        assert risky == 1.0
        assert safe == 0.0

    def test_settings_roundtrip(self) -> None:
        settings = Settings(
            PREDICTION_TEMPERATURE_WEIGHT=0.6,
            PREDICTION_CONFIDENCE_LIVE=0.95,
        )
        rules = PredictionRules.from_settings(settings)
        assert rules.temperature_weight == 0.6
        assert rules.confidence_live == 0.95
        assert rules.base_risk == 0.10


class TestHaversine:
    def test_identical_points_zero_distance(self) -> None:
        assert _haversine_km(18.9, 72.8, 18.9, 72.8) == 0.0

    def test_known_distance_mumbai_to_delhi(self) -> None:
        km = _haversine_km(19.076, 72.8777, 28.7041, 77.1025)
        assert 1100 <= km <= 1300


class TestPredictExcursionRisk:
    async def test_predicts_and_persists_prediction(self) -> None:
        repo = FakePredictionRepo()
        service = IntelligenceService(
            prediction_repo=repo,
            shipment_repo=_EmptyRepo(),  # type: ignore[arg-type]
            weather_service=FakeWeatherService(_snapshot(30.0, is_mock=True)),
            alert_repo=_EmptyRepo(),  # type: ignore[arg-type]
            warehouse_repo=_EmptyRepo(),  # type: ignore[arg-type]
            phc_repo=_EmptyRepo(),  # type: ignore[arg-type]
            container_repo=_EmptyRepo(),  # type: ignore[arg-type]
            rules=DEFAULT_RULES,
        )
        prediction = await service.predict_excursion_risk(_make_shipment())
        assert prediction.model_version == RULE_BASED_MODEL_VERSION
        assert 0.0 <= prediction.excursion_risk <= 1.0
        assert prediction.risk_level in {"low", "medium", "high", "critical"}
        assert prediction.confidence == DEFAULT_RULES.confidence_mock
        assert prediction.features["temperature_delta"] == 22.0
        assert len(repo.created) == 1

    async def test_live_weather_uses_live_confidence(self) -> None:
        service = _service(_snapshot(4.0, is_mock=False))
        prediction = await service.predict_excursion_risk(_make_shipment())
        assert prediction.confidence == DEFAULT_RULES.confidence_live
