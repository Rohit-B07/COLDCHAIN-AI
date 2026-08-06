"""Domain entities: Route and Waypoint.

A route is the planned execution of a shipment across one or more waypoints.
Waypoints are ordered stops (origin, transits, destination) with a sequence
index and expected arrival/departure estimates.

Routes carry optimization metadata (distance, duration, weather factor, safety
score, polyline, stops) and progress through a lifecycle: ``planned`` ->
``optimized`` -> ``selected`` (assigned to the shipment) -> ``completed``, or
``cancelled``.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4

ROUTE_STATUSES = ("planned", "optimized", "selected", "completed", "cancelled")
SELECTABLE_STATUSES = ("planned", "optimized", "selected")


@dataclass
class Waypoint:
    """A single ordered stop along a route."""

    waypoint_id: UUID
    route_id: UUID
    sequence: int
    name: str
    latitude: float
    longitude: float
    arrival_at: datetime | None = None
    departure_at: datetime | None = None

    @classmethod
    def create(
        cls,
        route_id: UUID,
        sequence: int,
        name: str,
        latitude: float,
        longitude: float,
        arrival_at: datetime | None = None,
        departure_at: datetime | None = None,
    ) -> "Waypoint":
        if not name:
            raise ValueError("waypoint name is required")
        if sequence < 0:
            raise ValueError("sequence must be non-negative")
        if not -90.0 <= latitude <= 90.0:
            raise ValueError("latitude must be between -90 and 90")
        if not -180.0 <= longitude <= 180.0:
            raise ValueError("longitude must be between -180 and 180")
        return cls(
            waypoint_id=uuid4(),
            route_id=route_id,
            sequence=sequence,
            name=name.strip(),
            latitude=latitude,
            longitude=longitude,
            arrival_at=arrival_at,
            departure_at=departure_at,
        )

    def update(
        self,
        sequence: int | None = None,
        name: str | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
        arrival_at: datetime | None = None,
        departure_at: datetime | None = None,
    ) -> None:
        """Apply waypoint edits; only the provided fields are changed."""
        if sequence is not None:
            if sequence < 0:
                raise ValueError("sequence must be non-negative")
            self.sequence = sequence
        if name is not None:
            if not name.strip():
                raise ValueError("waypoint name is required")
            self.name = name.strip()
        if latitude is not None:
            if not -90.0 <= latitude <= 90.0:
                raise ValueError("latitude must be between -90 and 90")
            self.latitude = latitude
        if longitude is not None:
            if not -180.0 <= longitude <= 180.0:
                raise ValueError("longitude must be between -180 and 180")
            self.longitude = longitude
        if arrival_at is not None:
            self.arrival_at = arrival_at
        if departure_at is not None:
            self.departure_at = departure_at


@dataclass
class Route:
    """A planned cold-chain delivery route for a shipment."""

    route_id: UUID
    shipment_id: UUID
    distance_km: float = 0.0
    duration_minutes: int = 0
    stops: list[dict] = field(default_factory=list)
    polyline: str = ""
    weather_factor: float = 1.0
    safety_score: float = 0.0
    is_selected: bool = False
    status: str = "planned"
    optimization_metadata: dict = field(default_factory=dict)
    waypoints: list[Waypoint] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    is_deleted: bool = False
    deleted_at: datetime | None = None

    @classmethod
    def create(
        cls,
        shipment_id: UUID,
        distance_km: float = 0.0,
        duration_minutes: int = 0,
        stops: list[dict] | None = None,
        polyline: str = "",
        weather_factor: float = 1.0,
        safety_score: float = 0.0,
        is_selected: bool = False,
        waypoints: list[Waypoint] | None = None,
        optimization_metadata: dict | None = None,
    ) -> "Route":
        cls.validate_metrics(
            distance_km=distance_km,
            duration_minutes=duration_minutes,
            weather_factor=weather_factor,
            safety_score=safety_score,
        )
        return cls(
            route_id=uuid4(),
            shipment_id=shipment_id,
            distance_km=distance_km,
            duration_minutes=duration_minutes,
            stops=list(stops or []),
            polyline=polyline,
            weather_factor=weather_factor,
            safety_score=safety_score,
            is_selected=is_selected,
            optimization_metadata=dict(optimization_metadata or {}),
            waypoints=list(waypoints or []),
        )

    @staticmethod
    def validate_metrics(
        *,
        distance_km: float,
        duration_minutes: int,
        weather_factor: float,
        safety_score: float,
    ) -> None:
        """Business rule: route metrics must lie within sane bounds."""
        if distance_km < 0:
            raise ValueError("distance_km must be non-negative")
        if duration_minutes < 0:
            raise ValueError("duration_minutes must be non-negative")
        if weather_factor <= 0:
            raise ValueError("weather_factor must be positive")
        if not 0.0 <= safety_score <= 100.0:
            raise ValueError("safety_score must be between 0 and 100")

    def update(
        self,
        distance_km: float | None = None,
        duration_minutes: int | None = None,
        stops: list[dict] | None = None,
        polyline: str | None = None,
        weather_factor: float | None = None,
        safety_score: float | None = None,
    ) -> None:
        """Apply route edits; only dispatched shipments' routes are locked."""
        if self.status == "completed":
            raise ValueError("cannot edit a completed route")
        new_distance = distance_km if distance_km is not None else self.distance_km
        new_duration = (
            duration_minutes if duration_minutes is not None else self.duration_minutes
        )
        new_weather = weather_factor if weather_factor is not None else self.weather_factor
        new_safety = safety_score if safety_score is not None else self.safety_score
        self.validate_metrics(
            distance_km=new_distance,
            duration_minutes=new_duration,
            weather_factor=new_weather,
            safety_score=new_safety,
        )
        self.distance_km = new_distance
        self.duration_minutes = new_duration
        if stops is not None:
            self.stops = list(stops)
        if polyline is not None:
            self.polyline = polyline
        self.weather_factor = new_weather
        self.safety_score = new_safety

    def add_waypoint(self, waypoint: Waypoint) -> None:
        self.waypoints.append(waypoint)
        self.waypoints.sort(key=lambda w: w.sequence)

    def mark_optimized(self, metadata: dict | None = None) -> None:
        """Record optimization metadata; the route may then be selected."""
        if self.status not in SELECTABLE_STATUSES:
            raise ValueError(
                f"cannot optimize a route in state {self.status!r}"
            )
        if metadata is not None:
            self.optimization_metadata = dict(metadata)
        self.status = "optimized"

    def select(self) -> None:
        """Assign this route as the chosen route for the shipment."""
        if self.status not in SELECTABLE_STATUSES:
            raise ValueError(
                f"cannot select a route in state {self.status!r}"
            )
        self.is_selected = True
        self.status = "selected"

    def deselect(self) -> None:
        self.is_selected = False
        if self.status == "selected":
            self.status = "optimized"

    def complete(self) -> None:
        if self.status != "selected":
            raise ValueError("only a selected route can be completed")
        self.status = "completed"

    def cancel(self) -> None:
        if self.status == "completed":
            raise ValueError("cannot cancel a completed route")
        self.status = "cancelled"

    def soft_delete(self) -> None:
        self.is_deleted = True
        self.deleted_at = datetime.now(UTC)
