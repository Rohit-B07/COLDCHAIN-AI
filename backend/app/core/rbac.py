"""Role-Based Access Control core engine (framework-agnostic).

Defines the canonical role catalog, role validation and the permission checker.
The permission matrix itself is declared in ``app.domain.permissions``; this
module maps concrete role names onto that matrix so enforcement stays in a
single place and the API layer remains declarative.
"""

import enum

from app.domain.permissions import ROLE_PERMISSIONS, Permission


class Role(str, enum.Enum):
    """Canonical platform roles (mirrors the seeded ``roles`` table)."""

    ADMIN = "admin"
    LOGISTICS_MANAGER = "logistics_manager"
    COLD_CHAIN_OPERATOR = "cold_chain_operator"
    DRIVER = "driver"
    AUDITOR = "auditor"

    @classmethod
    def from_value(cls, value: str) -> "Role":
        """Validate a role name and return the matching ``Role``.

        Raises ``ValueError`` for unknown or empty role names.
        """
        normalized = (value or "").strip().lower()
        try:
            return cls(normalized)
        except ValueError:
            raise ValueError(f"unknown role {value!r}") from None


def validate_role(value: str) -> Role:
    """Return the validated role for a raw role name.

    Convenience wrapper over ``Role.from_value`` kept for callers that expect a
    named role validator.
    """
    return Role.from_value(value)


def permissions_for(role: Role) -> frozenset[Permission]:
    """Return the permission set granted to a role.

    The catalog already grants every permission to ``admin``; unknown roles
    receive an empty set and therefore no access.
    """
    return ROLE_PERMISSIONS.get(role.value, frozenset())


def has_permission(role: Role | str, permission: Permission) -> bool:
    """Permission checker: report whether a role may perform an action."""
    resolved = Role.from_value(role) if isinstance(role, str) else role
    return permission in permissions_for(resolved)
