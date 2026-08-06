"""Route decorators that attach RBAC requirements to endpoint functions.

Decorators are declarative: they annotate the endpoint with the roles or
permissions it requires. Enforcement is performed either by the
``app.api.deps.rbac.enforce_rbac`` dependency (per-route, fine-grained) or by
the ``AuthorizationMiddleware`` (path-based, defense-in-depth).
"""

from collections.abc import Callable
from typing import TypeVar

from app.core.rbac import Role
from app.domain.permissions import Permission

PERMISSIONS_ATTR = "__rbac_required_permissions__"
ROLES_ATTR = "__rbac_required_roles__"

F = TypeVar("F", bound=Callable[..., object])


def require_permissions(*permissions: Permission) -> Callable[[F], F]:
    """Require the caller to hold every listed permission."""

    def decorator(func: F) -> F:
        existing = getattr(func, PERMISSIONS_ATTR, ())
        setattr(func, PERMISSIONS_ATTR, tuple(existing) + permissions)
        return func

    return decorator


def require_permission(permission: Permission) -> Callable[[F], F]:
    """Require the caller to hold a single permission."""
    return require_permissions(permission)


def require_roles(*roles: Role) -> Callable[[F], F]:
    """Require the caller to hold at least one of the listed roles."""

    def decorator(func: F) -> F:
        existing = getattr(func, ROLES_ATTR, ())
        setattr(func, ROLES_ATTR, tuple(existing) + roles)
        return func

    return decorator
