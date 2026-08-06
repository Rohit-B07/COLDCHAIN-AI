"""ORM models (infrastructure persistence layer).

These classes map domain aggregates to PostgreSQL tables. They are the ONLY
place where SQLAlchemy column definitions live. Domain entities stay pure;
mapping/adaptation is explicit and centralised.

Importing this module registers every model with `Base.metadata`, which Alembic
autogenerate and `create_all` rely on.
"""

from app.models.alert import AlertSeverity, AlertStatus, ColdAlert
from app.models.facility import PrimaryHealthCentre, Warehouse
from app.models.logistics import (
    ColdContainer,
    ContainerStatus,
    Driver,
    DriverStatus,
    Vehicle,
    VehicleStatus,
    VehicleType,
)
from app.models.prediction import Prediction
from app.models.role import Role, user_roles
from app.models.route import Route, Waypoint
from app.models.shipment import Priority, Shipment, ShipmentStatus
from app.models.user import RefreshToken, User, UserRole
from app.models.weather import WeatherCache

__all__ = [
    "AlertSeverity",
    "AlertStatus",
    "ColdAlert",
    "ColdContainer",
    "ContainerStatus",
    "Driver",
    "DriverStatus",
    "Prediction",
    "PrimaryHealthCentre",
    "Priority",
    "RefreshToken",
    "Role",
    "Route",
    "Shipment",
    "ShipmentStatus",
    "User",
    "UserRole",
    "Vehicle",
    "VehicleStatus",
    "VehicleType",
    "Warehouse",
    "Waypoint",
    "WeatherCache",
    "user_roles",
]
