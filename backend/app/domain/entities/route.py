"""Domain entities: Route and Waypoint.

A route is the planned execution of a shipment across one or more waypoints.
Waypoints are ordered stops (origin, transits, destination) with a sequence
index and expected arrival/departure estimates.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4


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
    waypoints: list[Waypoint] = field(default_factory=list)

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
    ) -> "Route":
        if distance_km < 0:
            raise ValueError("distance_km must be non-negative")
        if duration_minutes < 0:
            raise ValueError("duration_minutes must be non-negative")
        if weather_factor <= 0:
            raise ValueError("weather_factor must be positive")
        if not 0.0 <= safety_score <= 100.0:
            raise ValueError("safety_score must be between 0 and 100")
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
            waypoints=list(waypoints or []),
        )

    def add_waypoint(self, waypoint: Waypoint) -> None:
        self.waypoints.append(waypoint)
        self.waypoints.sort(key=lambda w: w.sequence)

    @property
    def created_at(self) -> datetime:
        return datetime.now(UTC)
