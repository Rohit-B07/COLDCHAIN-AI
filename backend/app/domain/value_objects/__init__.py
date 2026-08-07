"""Domain value objects and enums shared across aggregates."""

import enum
from dataclasses import dataclass, field

ABSOLUTE_ZERO_C = -273.15
MIN_LATITUDE = -90.0
MAX_LATITUDE = 90.0
MIN_LONGITUDE = -180.0
MAX_LONGITUDE = 180.0
EXCURSION_REPORT_RISK_LEVELS = ("low", "medium", "high")


class UserRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    DISPATCHER = "dispatcher"
    LOGISTICS = "logistics"
    DRIVER = "driver"


class ShipmentStatus(str, enum.Enum):
    CREATED = "created"
    PREDICTED = "predicted"
    DISPATCHED = "dispatched"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class Priority(str, enum.Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RiskLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class TemperatureReading:
    """A single temperature observation with a recorded timestamp."""

    celsius: float
    recorded_at: str

    def __post_init__(self) -> None:
        if self.celsius < ABSOLUTE_ZERO_C:
            raise ValueError(
                f"celsius cannot be below absolute zero ({ABSOLUTE_ZERO_C}°C)"
            )
        if not self.recorded_at:
            raise ValueError("recorded_at is required")


@dataclass(frozen=True)
class GeoCoordinate:
    """A latitude/longitude pair with range validation."""

    latitude: float
    longitude: float

    def __post_init__(self) -> None:
        if not MIN_LATITUDE <= self.latitude <= MAX_LATITUDE:
            raise ValueError(
                f"latitude must be between {MIN_LATITUDE} and {MAX_LATITUDE}"
            )
        if not MIN_LONGITUDE <= self.longitude <= MAX_LONGITUDE:
            raise ValueError(
                f"longitude must be between {MIN_LONGITUDE} and {MAX_LONGITUDE}"
            )


@dataclass(frozen=True)
class ExcursionReport:
    """A human-facing risk report card for a shipment.

    Uses a simplified three-level scale (low/medium/high) even though the
    persisted ``Prediction`` carries a four-level risk. The reduced scale keeps
    the report easy to scan while the full model remains available in the API.
    """

    predicted: bool
    confidence: float
    risk_level: str
    contributing_factors: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")
        if self.risk_level not in EXCURSION_REPORT_RISK_LEVELS:
            raise ValueError(
                "risk_level must be one of "
                + ", ".join(EXCURSION_REPORT_RISK_LEVELS)
            )
