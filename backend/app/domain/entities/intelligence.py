"""Domain entities for routing, prediction, weather and alerts."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4


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


RISK_LEVELS = ("low", "medium", "high", "critical")


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

    @classmethod
    def create(
        cls,
        *,
        shipment_id: UUID,
        excursion_risk: float,
        risk_level: str,
        confidence: float,
        expected_min_temp: float,
        expected_max_temp: float,
        model_version: str,
        features: dict | None = None,
        explanations: dict | None = None,
    ) -> "Prediction":
        validate_risk_metrics(
            excursion_risk=excursion_risk,
            risk_level=risk_level,
            confidence=confidence,
            expected_min_temp=expected_min_temp,
            expected_max_temp=expected_max_temp,
            model_version=model_version,
        )
        return cls(
            prediction_id=uuid4(),
            shipment_id=shipment_id,
            excursion_risk=excursion_risk,
            risk_level=risk_level,
            confidence=confidence,
            expected_min_temp=expected_min_temp,
            expected_max_temp=expected_max_temp,
            model_version=model_version,
            features=features or {},
            explanations=explanations or {},
            created_at=datetime.now(UTC),
        )

    def update(
        self,
        *,
        excursion_risk: float | None = None,
        risk_level: str | None = None,
        confidence: float | None = None,
        expected_min_temp: float | None = None,
        expected_max_temp: float | None = None,
        model_version: str | None = None,
        features: dict | None = None,
        explanations: dict | None = None,
    ) -> None:
        validate_risk_metrics(
            excursion_risk=excursion_risk if excursion_risk is not None else self.excursion_risk,
            risk_level=risk_level if risk_level is not None else self.risk_level,
            confidence=confidence if confidence is not None else self.confidence,
            expected_min_temp=expected_min_temp if expected_min_temp is not None else self.expected_min_temp,
            expected_max_temp=expected_max_temp if expected_max_temp is not None else self.expected_max_temp,
            model_version=model_version if model_version is not None else self.model_version,
        )
        if excursion_risk is not None:
            self.excursion_risk = excursion_risk
        if risk_level is not None:
            self.risk_level = risk_level
        if confidence is not None:
            self.confidence = confidence
        if expected_min_temp is not None:
            self.expected_min_temp = expected_min_temp
        if expected_max_temp is not None:
            self.expected_max_temp = expected_max_temp
        if model_version is not None:
            self.model_version = model_version
        if features is not None:
            self.features = features
        if explanations is not None:
            self.explanations = explanations


def validate_risk_metrics(
    *,
    excursion_risk: float,
    risk_level: str,
    confidence: float,
    expected_min_temp: float,
    expected_max_temp: float,
    model_version: str,
) -> None:
    if not 0.0 <= excursion_risk <= 1.0:
        raise ValueError("excursion_risk must be between 0.0 and 1.0")
    if risk_level not in RISK_LEVELS:
        raise ValueError(f"risk_level must be one of {', '.join(RISK_LEVELS)}")
    if not 0.0 <= confidence <= 1.0:
        raise ValueError("confidence must be between 0.0 and 1.0")
    if expected_min_temp > expected_max_temp:
        raise ValueError("expected_min_temp must be <= expected_max_temp")
    if not model_version.strip():
        raise ValueError("model_version must not be empty")


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
    source: str = "mock"
    forecast: dict = field(default_factory=dict)
    fetched_at: datetime | None = None
    expires_at: datetime | None = None


ALERT_SEVERITIES = ("info", "warning", "critical")
ALERT_STATUSES = ("open", "acknowledged", "resolved")
ACKNOWLEDGEABLE_STATUSES = ("open",)


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
    acknowledged_by: UUID | None = None
    acknowledged_at: datetime | None = None
    created_at: datetime | None = None

    @classmethod
    def create(
        cls,
        *,
        severity: str,
        alert_type: str,
        message: str,
        shipment_id: UUID | None = None,
        container_id: UUID | None = None,
    ) -> "ColdAlert":
        validate_alert_fields(
            severity=severity,
            alert_type=alert_type,
            message=message,
        )
        return cls(
            alert_id=uuid4(),
            severity=severity,
            alert_type=alert_type,
            message=message,
            shipment_id=shipment_id,
            container_id=container_id,
            status="open",
            created_at=datetime.now(UTC),
        )

    def update(
        self,
        *,
        severity: str | None = None,
        alert_type: str | None = None,
        message: str | None = None,
    ) -> None:
        validate_alert_fields(
            severity=severity if severity is not None else self.severity,
            alert_type=alert_type if alert_type is not None else self.alert_type,
            message=message if message is not None else self.message,
        )
        if severity is not None:
            self.severity = severity
        if alert_type is not None:
            self.alert_type = alert_type
        if message is not None:
            self.message = message

    def acknowledge(self, user_id: UUID) -> None:
        if self.status not in ACKNOWLEDGEABLE_STATUSES:
            raise ValueError("Only open alerts can be acknowledged")
        self.status = "acknowledged"
        self.acknowledged_by = user_id
        self.acknowledged_at = datetime.now(UTC)

    def resolve(self) -> None:
        if self.status == "resolved":
            raise ValueError("Alert is already resolved")
        if self.status not in ("open", "acknowledged"):
            raise ValueError("Only open or acknowledged alerts can be resolved")
        self.status = "resolved"


def validate_alert_fields(
    *,
    severity: str,
    alert_type: str,
    message: str,
) -> None:
    if severity not in ALERT_SEVERITIES:
        raise ValueError(f"severity must be one of {', '.join(ALERT_SEVERITIES)}")
    if not alert_type.strip():
        raise ValueError("alert_type must not be empty")
    if len(alert_type) > 64:
        raise ValueError("alert_type must be at most 64 characters")
    if not message.strip():
        raise ValueError("message must not be empty")
