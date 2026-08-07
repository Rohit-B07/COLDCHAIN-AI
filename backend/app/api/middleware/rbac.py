"""Authorization middleware: centralized, path-based RBAC enforcement.

Guards protected URL prefixes with the permission they require. The middleware
runs before routing, so a request to a protected path is denied (401/403)
without ever reaching an endpoint when the caller lacks the required
permission. This is defense-in-depth: it works regardless of whether individual
routes also attach ``app.api.decorators`` requirements.

Policy entries map ``(HTTP method, path prefix)`` to a permission; the longest
matching prefix wins. ``/api/v1/auth`` endpoints are intentionally not listed
and therefore remain public (login, register, token refresh, etc.).
"""

import logging
from uuid import UUID

from jwt import InvalidTokenError
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from app.api.deps.rbac import resolve_user_roles
from app.core.rbac import permissions_for
from app.core.security import decode_token
from app.db.session import async_session_factory
from app.domain.permissions import Permission
from app.repositories.role import SqlAlchemyRoleRepository
from app.repositories.user import SqlAlchemyUserRepository

logger = logging.getLogger("coldchain.api.middleware.rbac")

RBAC_PATH_POLICY: dict[tuple[str, str], Permission | None] = {
    ("GET", "/api/v1/shipments"): Permission.SHIPMENT_VIEW,
    ("POST", "/api/v1/shipments"): Permission.SHIPMENT_CREATE,
    ("PATCH", "/api/v1/shipments"): Permission.SHIPMENT_UPDATE,
    ("DELETE", "/api/v1/shipments"): Permission.SHIPMENT_DELETE,
    ("GET", "/api/v1/routes"): Permission.ROUTE_VIEW,
    ("POST", "/api/v1/routes"): Permission.ROUTE_PLAN,
    ("PATCH", "/api/v1/routes"): Permission.ROUTE_UPDATE,
    ("DELETE", "/api/v1/routes"): Permission.ROUTE_UPDATE,
    ("GET", "/api/v1/facilities"): Permission.FACILITY_VIEW,
    ("POST", "/api/v1/facilities"): Permission.FACILITY_MANAGE,
    ("PATCH", "/api/v1/facilities"): Permission.FACILITY_MANAGE,
    ("GET", "/api/v1/warehouses"): Permission.FACILITY_VIEW,
    ("POST", "/api/v1/warehouses"): Permission.FACILITY_MANAGE,
    ("PATCH", "/api/v1/warehouses"): Permission.FACILITY_MANAGE,
    ("DELETE", "/api/v1/warehouses"): Permission.FACILITY_MANAGE,
    ("GET", "/api/v1/phcs"): Permission.FACILITY_VIEW,
    ("POST", "/api/v1/phcs"): Permission.FACILITY_MANAGE,
    ("PATCH", "/api/v1/phcs"): Permission.FACILITY_MANAGE,
    ("DELETE", "/api/v1/phcs"): Permission.FACILITY_MANAGE,
    ("GET", "/api/v1/logistics"): Permission.LOGISTICS_VIEW,
    ("POST", "/api/v1/logistics"): Permission.LOGISTICS_MANAGE,
    ("PATCH", "/api/v1/logistics"): Permission.LOGISTICS_MANAGE,
    ("GET", "/api/v1/drivers"): Permission.LOGISTICS_VIEW,
    ("POST", "/api/v1/drivers"): Permission.LOGISTICS_MANAGE,
    ("PATCH", "/api/v1/drivers"): Permission.LOGISTICS_MANAGE,
    ("DELETE", "/api/v1/drivers"): Permission.LOGISTICS_MANAGE,
    ("GET", "/api/v1/vehicles"): Permission.LOGISTICS_VIEW,
    ("POST", "/api/v1/vehicles"): Permission.LOGISTICS_MANAGE,
    ("PATCH", "/api/v1/vehicles"): Permission.LOGISTICS_MANAGE,
    ("DELETE", "/api/v1/vehicles"): Permission.LOGISTICS_MANAGE,
    ("GET", "/api/v1/containers"): Permission.CONTAINER_VIEW,
    ("POST", "/api/v1/containers"): Permission.CONTAINER_MANAGE,
    ("PATCH", "/api/v1/containers"): Permission.CONTAINER_MANAGE,
    ("GET", "/api/v1/predictions"): Permission.PREDICTION_VIEW,
    ("POST", "/api/v1/predictions"): Permission.PREDICTION_MANAGE,
    ("PATCH", "/api/v1/predictions"): Permission.PREDICTION_MANAGE,
    ("DELETE", "/api/v1/predictions"): Permission.PREDICTION_MANAGE,
    ("GET", "/api/v1/alerts"): Permission.ALERT_VIEW,
    ("POST", "/api/v1/alerts"): Permission.ALERT_MANAGE,
    ("POST", "/api/v1/alerts/"): Permission.ALERT_ACKNOWLEDGE,
    ("PATCH", "/api/v1/alerts"): Permission.ALERT_ACKNOWLEDGE,
    ("DELETE", "/api/v1/alerts"): Permission.ALERT_MANAGE,
    ("GET", "/api/v1/notifications"): Permission.ALERT_VIEW,
    ("GET", "/api/v1/analytics"): Permission.ALERT_VIEW,
    ("GET", "/api/v1/audit"): Permission.AUDIT_VIEW,
    ("GET", "/api/v1/weather"): Permission.WEATHER_VIEW,
    ("GET", "/api/v1/users/me"): None,
    ("PATCH", "/api/v1/users/me"): None,
    ("POST", "/api/v1/users/me/change-password"): None,
    ("GET", "/api/v1/users"): Permission.USER_MANAGE,
    ("POST", "/api/v1/users"): Permission.USER_MANAGE,
    ("PATCH", "/api/v1/users"): Permission.USER_MANAGE,
    ("GET", "/api/v1/roles"): Permission.ROLE_MANAGE,
}


class AuthorizationMiddleware:
    """Enforce the RBAC path policy and short-circuit unauthorized requests."""

    def __init__(
        self,
        app: ASGIApp,
        policy: dict[tuple[str, str], Permission | None] | None = None,
    ) -> None:
        self.app = app
        self.policy = policy if policy is not None else RBAC_PATH_POLICY

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        required = self._required_permission(scope)
        if required is None:
            await self.app(scope, receive, send)
            return

        token = self._bearer_token(scope)
        if token is None:
            await self._deny(
                scope,
                receive,
                send,
                401,
                "authentication_failed",
                "Missing bearer token",
            )
            return

        try:
            payload = decode_token(token)
            user_id = UUID(payload["sub"])
        except (InvalidTokenError, KeyError, ValueError):
            await self._deny(
                scope,
                receive,
                send,
                401,
                "token_expired",
                "Token is invalid or expired",
            )
            return
        if payload.get("type") != "access":
            await self._deny(
                scope,
                receive,
                send,
                401,
                "token_expired",
                "Token is not an access token",
            )
            return

        granted: set[Permission] = set()
        async with async_session_factory() as session:
            user = await SqlAlchemyUserRepository(session).get_by_id(user_id)
            if user is None or not user.is_active:
                await self._deny(
                    scope,
                    receive,
                    send,
                    401,
                    "authentication_failed",
                    "Account no longer valid",
                )
                return
            roles = await resolve_user_roles(user, SqlAlchemyRoleRepository(session))
            for role in roles:
                granted.update(permissions_for(role))

        if required not in granted:
            await self._deny(
                scope,
                receive,
                send,
                403,
                "forbidden",
                "You do not have permission to perform this action",
            )
            return

        await self.app(scope, receive, send)

    def _required_permission(self, scope: Scope) -> Permission | None:
        """Resolve the permission required for a request, if any.

        A ``None`` value in the policy explicitly grants pass-through (no
        permission gate, e.g. a user managing their own profile), overriding
        any shorter matching prefix.
        """
        method = scope.get("method", "GET")
        path = scope.get("path", "")
        best: tuple[int, Permission | None] | None = None
        for (policy_method, prefix), permission in self.policy.items():
            if policy_method != method:
                continue
            if not path.startswith(prefix):
                continue
            if best is None or len(prefix) > best[0]:
                best = (len(prefix), permission)
        return best[1] if best is not None else None

    def _bearer_token(self, scope: Scope) -> str | None:
        """Extract the ``Bearer`` token from the request headers, if any."""
        headers: list[tuple[bytes, bytes]] = scope.get("headers", [])
        for name, value in headers:
            if name.lower() != b"authorization":
                continue
            scheme, _, token = value.decode("latin-1").partition(" ")
            if scheme.lower() == "bearer" and token:
                return token
        return None

    async def _deny(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
        status_code: int,
        error_code: str,
        message: str,
    ) -> None:
        """Send a structured denial response in the standard error envelope."""
        logger.warning("RBAC denied %s %s: %s", scope.get("method"), scope.get("path"), error_code)
        response = JSONResponse(
            status_code=status_code,
            content={
                "success": False,
                "error_code": error_code,
                "message": message,
                "details": [],
            },
        )
        await response(scope, receive, send)
