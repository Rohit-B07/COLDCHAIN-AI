"""Route and waypoint DTOs."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

RouteStatusValue = Literal["planned", "optimized", "selected", "completed", "cancelled"]


class WaypointCreate(BaseModel):
    sequence: int = Field(ge=0)
    name: str = Field(min_length=1, max_length=255)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    arrival_at: datetime | None = None
    departure_at: datetime | None = None


class WaypointUpdate(BaseModel):
    sequence: int | None = Field(default=None, ge=0)
    name: str | None = Field(default=None, min_length=1, max_length=255)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
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
    optimization_metadata: dict = Field(default_factory=dict)

    @field_validator("polyline", mode="before")
    @classmethod
    def strip_polyline(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value


class RouteUpdate(BaseModel):
    distance_km: float | None = Field(default=None, ge=0)
    duration_minutes: int | None = Field(default=None, ge=0)
    stops: list[dict] | None = None
    polyline: str | None = Field(default=None, max_length=1000)
    weather_factor: float | None = Field(default=None, gt=0)
    safety_score: float | None = Field(default=None, ge=0, le=100)

    @field_validator("polyline", mode="before")
    @classmethod
    def strip_polyline(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value


class RouteStatusUpdate(BaseModel):
    status: RouteStatusValue


class RouteOptimizeUpdate(BaseModel):
    distance_km: float | None = Field(default=None, ge=0)
    duration_minutes: int | None = Field(default=None, ge=0)
    stops: list[dict] | None = None
    polyline: str | None = Field(default=None, max_length=1000)
    weather_factor: float | None = Field(default=None, gt=0)
    safety_score: float | None = Field(default=None, ge=0, le=100)
    optimization_metadata: dict | None = None


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
    status: RouteStatusValue
    optimization_metadata: dict = Field(default_factory=dict)
    waypoints: list[WaypointRead] = Field(default_factory=list)
    is_deleted: bool = False
    created_at: datetime | None = None


class RouteQueryParams(BaseModel):
    """Query params for listing and filtering routes."""

    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)
    shipment_id: UUID | None = None
    status: RouteStatusValue | None = None
    is_selected: bool | None = None
