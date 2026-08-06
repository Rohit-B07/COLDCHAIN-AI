"""RBAC FastAPI dependencies.

Resolves the roles a current user holds and exposes dependency factories that
enforce role and permission requirements on routes. Role resolution prefers
explicit links from the ``roles`` table (via ``user_roles``) and falls back to
the role recorded on the user's own account when no links exist, so newly
created users remain functional.
"""

from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, Request

from app.api.deps.auth import CurrentUser
from app.api.deps.container import get_role_repository
from app.core.exceptions import AuthorizationError
from app.core.rbac import Role, permissions_for
from app.domain.entities.user import User
from app.domain.permissions import Permission
from app.domain.repositories import RoleRepository
from app.domain.value_objects import UserRole

# Legacy user-record roles -> canonical RBAC role. Used only as a fallback when
# a user has no explicit links in the ``user_roles`` table.
USERROLE_TO_RBAC_ROLE: dict[UserRole, Role] = {
    UserRole.SUPER_ADMIN: Role.ADMIN,
    UserRole.ADMIN: Role.ADMIN,
    UserRole.DISPATCHER: Role.LOGISTICS_MANAGER,
    UserRole.LOGISTICS: Role.LOGISTICS_MANAGER,
    UserRole.DRIVER: Role.DRIVER,
}


async def resolve_user_roles(user: User, roles: RoleRepository) -> frozenset[Role]:
    """Resolve the canonical RBAC roles held by a user.

    Explicit role links take precedence; users without links fall back to the
    single role recorded on their account. Unknown role names are ignored
    defensively so a stale row can never escalate permissions.
    """
    granted: set[Role] = set()
    for role in await roles.get_roles_for_user(user.user_id):
        try:
            granted.add(Role.from_value(role.name))
        except ValueError:
            continue
    if not granted:
        fallback = USERROLE_TO_RBAC_ROLE.get(user.role)
        if fallback is not None:
            granted.add(fallback)
    return frozenset(granted)


async def get_user_roles(
    user: CurrentUser,
    roles: Annotated[RoleRepository, Depends(get_role_repository)],
) -> frozenset[Role]:
    """FastAPI dependency resolving the current user's role set."""
    return await resolve_user_roles(user, roles)


CurrentUserRoles = Annotated[frozenset[Role], Depends(get_user_roles)]


def require_roles(*roles: Role) -> Callable[..., frozenset[Role]]:
    """Dependency factory: require the caller to hold at least one role."""

    def _check(current_roles: CurrentUserRoles) -> frozenset[Role]:
        if not current_roles & set(roles):
            raise AuthorizationError("You do not have permission to perform this action")
        return current_roles

    return _check


def require_permissions(*permissions: Permission) -> Callable[..., frozenset[Role]]:
    """Dependency factory: require the caller to hold every permission."""

    def _check(current_roles: CurrentUserRoles) -> frozenset[Role]:
        granted = {
            permission
            for role in current_roles
            for permission in permissions_for(role)
        }
        if not set(permissions) <= granted:
            raise AuthorizationError("You do not have permission to perform this action")
        return current_roles

    return _check


async def enforce_rbac(
    request: Request,
    current_roles: CurrentUserRoles,
) -> None:
    """Dependency enforcing route-decorator RBAC metadata.

    Reads the requirements attached by ``app.api.decorators`` to the matched
    endpoint and raises ``AuthorizationError`` (403) when they are unmet.
    """
    route = request.scope.get("route")
    endpoint = getattr(route, "endpoint", None) if route is not None else None
    required_permissions = getattr(endpoint, "__rbac_required_permissions__", ())
    required_roles = getattr(endpoint, "__rbac_required_roles__", ())

    if required_permissions:
        granted = {
            permission
            for role in current_roles
            for permission in permissions_for(role)
        }
        if not set(required_permissions) <= granted:
            raise AuthorizationError("You do not have permission to perform this action")
    if required_roles and not current_roles & set(required_roles):
        raise AuthorizationError("You do not have permission to perform this action")


EnforceRbac = Annotated[None, Depends(enforce_rbac)]
