"""Pure domain entities.

Entities are the core business objects of the domain. They are plain Python
classes with no dependency on FastAPI, SQLAlchemy, or Pydantic. Persistence
details live in `app.models` (ORM) which is intentionally kept separate.
"""

from app.domain.entities.facility import PrimaryHealthCentre, Warehouse
from app.domain.entities.intelligence import (
    ColdAlert,
    Prediction,
    WarmRoute,
    WeatherSnapshot,
)
from app.domain.entities.logistics import ColdContainer, Driver, Vehicle
from app.domain.entities.role import Role
from app.domain.entities.route import Route, Waypoint
from app.domain.entities.shipment import Shipment
from app.domain.entities.user import User

__all__ = [
    "ColdAlert",
    "ColdContainer",
    "Driver",
    "Prediction",
    "PrimaryHealthCentre",
    "Role",
    "Route",
    "Shipment",
    "User",
    "Vehicle",
    "Warehouse",
    "Waypoint",
    "WeatherSnapshot",
    "WarmRoute",
]
