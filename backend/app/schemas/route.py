"""Route and waypoint DTOs."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class WaypointCreate(BaseModel):
    sequence: int = Field(ge=0)
    name: str = Field(min_length=1, max_length=255)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    arrival_at: datetime | None = None
    departure_at: datetime | None = None


class WaypointRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    route_id: UUID
    sequence: int
    name: str
    latitude: float
    longitude: float
    arrival_at: datetime | None
    departure_at: datetime | None


class RouteCreate(BaseModel):
    shipment_id: UUID
    distance_km: float = Field(default=0.0, ge=0)
    duration_minutes: int = Field(default=0, ge=0)
    stops: list[dict] = Field(default_factory=list)
    polyline: str = Field(default="", max_length=1000)
    weather_factor: float = Field(default=1.0, gt=0)
    safety_score: float = Field(default=0.0, ge=0, le=100)
    is_selected: bool = False
    waypoints: list[WaypointCreate] = Field(default_factory=list)

    @field_validator("polyline", mode="before")
    @classmethod
    def strip_polyline(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value


class RouteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    shipment_id: UUID
    distance_km: float
    duration_minutes: int
    stops: list[dict]
    polyline: str
    weather_factor: float
    safety_score: float
    is_selected: bool
    waypoints: list[WaypointRead] = Field(default_factory=list)
