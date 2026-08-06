"""Authorization catalog: default permissions and their role assignments.

Permissions are declared as code-level constants rather than database rows.
This keeps the authorization matrix auditable in a single place and trivially
idempotent (constants cannot be inserted twice). The catalog is consumed by the
authorization layer and referenced by the database seeder.
"""

import enum


class Permission(str, enum.Enum):
    """Granular, resource-scoped permission codes used for authorization."""

    DASHBOARD_VIEW = "dashboard:view"
    SHIPMENT_VIEW = "shipment:view"
    SHIPMENT_CREATE = "shipment:create"
    SHIPMENT_UPDATE = "shipment:update"
    SHIPMENT_DISPATCH = "shipment:dispatch"
    SHIPMENT_DELETE = "shipment:delete"
    ROUTE_VIEW = "route:view"
    ROUTE_PLAN = "route:plan"
    ROUTE_UPDATE = "route:update"
    ROUTE_SELECT = "route:select"
    FACILITY_VIEW = "facility:view"
    FACILITY_MANAGE = "facility:manage"
    LOGISTICS_VIEW = "logistics:view"
    LOGISTICS_MANAGE = "logistics:manage"
    CONTAINER_VIEW = "container:view"
    CONTAINER_MANAGE = "container:manage"
    PREDICTION_VIEW = "prediction:view"
    PREDICTION_MANAGE = "prediction:manage"
    ALERT_VIEW = "alert:view"
    ALERT_ACKNOWLEDGE = "alert:acknowledge"
    ALERT_MANAGE = "alert:manage"
    WEATHER_VIEW = "weather:view"
    AUDIT_VIEW = "audit:view"
    USER_MANAGE = "user:manage"
    ROLE_MANAGE = "role:manage"


ROLE_DESCRIPTIONS: dict[str, str] = {
    "admin": "Full platform administration, including users, roles and audit.",
    "logistics_manager": "End-to-end management of shipments, routes, facilities and assets.",
    "cold_chain_operator": "Operates containers and monitors telemetry, predictions and alerts.",
    "driver": "Executes assigned deliveries and reports route and status updates.",
    "auditor": "Read-only access across the platform for compliance and auditing.",
}


ROLE_PERMISSIONS: dict[str, frozenset[Permission]] = {
    "admin": frozenset(Permission),
    "logistics_manager": frozenset(
        {
            Permission.SHIPMENT_VIEW,
            Permission.SHIPMENT_CREATE,
            Permission.SHIPMENT_UPDATE,
            Permission.SHIPMENT_DISPATCH,
            Permission.ROUTE_VIEW,
            Permission.ROUTE_PLAN,
            Permission.ROUTE_SELECT,
            Permission.FACILITY_VIEW,
            Permission.FACILITY_MANAGE,
            Permission.LOGISTICS_VIEW,
            Permission.LOGISTICS_MANAGE,
            Permission.CONTAINER_VIEW,
            Permission.CONTAINER_MANAGE,
            Permission.PREDICTION_VIEW,
            Permission.ALERT_VIEW,
            Permission.ALERT_ACKNOWLEDGE,
            Permission.WEATHER_VIEW,
        }
    ),
    "cold_chain_operator": frozenset(
        {
            Permission.SHIPMENT_VIEW,
            Permission.SHIPMENT_UPDATE,
            Permission.ROUTE_VIEW,
            Permission.CONTAINER_VIEW,
            Permission.CONTAINER_MANAGE,
            Permission.PREDICTION_VIEW,
            Permission.PREDICTION_MANAGE,
            Permission.ALERT_VIEW,
            Permission.ALERT_ACKNOWLEDGE,
            Permission.ALERT_MANAGE,
            Permission.WEATHER_VIEW,
        }
    ),
    "driver": frozenset(
        {
            Permission.SHIPMENT_VIEW,
            Permission.ROUTE_VIEW,
            Permission.ROUTE_UPDATE,
            Permission.CONTAINER_VIEW,
            Permission.ALERT_VIEW,
            Permission.ALERT_ACKNOWLEDGE,
        }
    ),
    "auditor": frozenset(
        {
            Permission.DASHBOARD_VIEW,
            Permission.SHIPMENT_VIEW,
            Permission.ROUTE_VIEW,
            Permission.FACILITY_VIEW,
            Permission.LOGISTICS_VIEW,
            Permission.CONTAINER_VIEW,
            Permission.PREDICTION_VIEW,
            Permission.ALERT_VIEW,
            Permission.WEATHER_VIEW,
            Permission.AUDIT_VIEW,
        }
    ),
}


DEFAULT_ROLES: tuple[str, ...] = tuple(ROLE_DESCRIPTIONS)
