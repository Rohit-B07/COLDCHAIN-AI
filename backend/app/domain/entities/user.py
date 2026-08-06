"""Pure domain entity: User.

The entity carries identity and RBAC role. Password hashing and JWT issuing are
infrastructure concerns handled in `app.services` / `app.core.security`; this
class only models the aggregate state.
"""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4

from app.domain.value_objects import UserRole


@dataclass
class User:
    """A registered platform user."""

    user_id: UUID
    email: str
    full_name: str
    password_hash: str
    role: UserRole
    is_active: bool = True
    created_at: datetime | None = None

    @classmethod
    def create(
        cls,
        email: str,
        full_name: str,
        password_hash: str,
        role: UserRole = UserRole.LOGISTICS,
    ) -> "User":
        if not email or not full_name or not password_hash:
            raise ValueError("email, full_name and password_hash are required")
        return cls(
            user_id=uuid4(),
            email=email.lower().strip(),
            full_name=full_name.strip(),
            password_hash=password_hash,
            role=role,
        )

    def deactivate(self) -> None:
        self.is_active = False

    def activate(self) -> None:
        self.is_active = True

    def update_profile(self, full_name: str | None = None, email: str | None = None) -> None:
        """Apply profile edits; only the provided fields are changed."""
        if full_name is not None:
            self.full_name = full_name.strip()
        if email is not None:
            self.email = email.strip().lower()

    def change_password(self, new_password_hash: str) -> None:
        """Replace the stored password hash."""
        self.password_hash = new_password_hash
