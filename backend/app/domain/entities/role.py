"""Pure domain entity: Role."""

from dataclasses import dataclass
from uuid import UUID, uuid4


@dataclass
class Role:
    """A discrete access-control role."""

    role_id: UUID
    name: str
    description: str = ""
    is_deleted: bool = False

    @classmethod
    def create(cls, name: str, description: str = "") -> "Role":
        if not name or not name.strip():
            raise ValueError("role name is required")
        normalized = name.strip().lower()
        if " " in normalized:
            raise ValueError("role name must not contain spaces")
        return cls(
            role_id=uuid4(),
            name=normalized,
            description=description.strip(),
        )

    def soft_delete(self) -> None:
        self.is_deleted = True

    def restore(self) -> None:
        self.is_deleted = False
