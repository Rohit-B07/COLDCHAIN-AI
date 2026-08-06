"""Domain entities for facilities (warehouse / primary health centre)."""

import re
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4

MIN_CAPACITY = 1
MAX_CAPACITY = 1_000_000
CODE_PATTERN = re.compile(r"^[A-Z0-9][A-Z0-9_-]*$")


@dataclass
class Warehouse:
    warehouse_id: UUID
    name: str
    code: str
    latitude: float
    longitude: float
    address: str = ""
    capacity: int = MIN_CAPACITY
    is_deleted: bool = False
    created_at: datetime | None = None

    @staticmethod
    def validate_capacity(capacity: int) -> None:
        """Business rule: a warehouse must have a positive, bounded capacity."""
        if capacity < MIN_CAPACITY or capacity > MAX_CAPACITY:
            raise ValueError(
                f"capacity must be between {MIN_CAPACITY} and {MAX_CAPACITY}"
            )

    @classmethod
    def create(
        cls,
        name: str,
        code: str,
        latitude: float,
        longitude: float,
        address: str = "",
        capacity: int = MIN_CAPACITY,
    ) -> "Warehouse":
        if not name or not code:
            raise ValueError("name and code are required")
        normalized_code = code.strip().upper()
        if not CODE_PATTERN.match(normalized_code):
            raise ValueError(
                "code must contain only letters, digits, dashes or underscores"
            )
        cls.validate_capacity(capacity)
        return cls(
            warehouse_id=uuid4(),
            name=name.strip(),
            code=normalized_code,
            latitude=latitude,
            longitude=longitude,
            address=address,
            capacity=capacity,
        )

    def update(
        self,
        name: str | None = None,
        code: str | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
        address: str | None = None,
        capacity: int | None = None,
    ) -> None:
        """Apply warehouse edits; only the provided fields are changed."""
        if name is not None:
            if not name.strip():
                raise ValueError("name is required")
            self.name = name.strip()
        if code is not None:
            normalized_code = code.strip().upper()
            if not CODE_PATTERN.match(normalized_code):
                raise ValueError(
                    "code must contain only letters, digits, dashes or underscores"
                )
            self.code = normalized_code
        if latitude is not None:
            self.latitude = latitude
        if longitude is not None:
            self.longitude = longitude
        if address is not None:
            self.address = address.strip()
        if capacity is not None:
            self.validate_capacity(capacity)
            self.capacity = capacity

    def soft_delete(self) -> None:
        self.is_deleted = True


@dataclass
class PrimaryHealthCentre:
    phc_id: UUID
    name: str
    code: str
    district: str
    state: str
    latitude: float
    longitude: float
    contact: str = ""
    capacity: int = MIN_CAPACITY
    priority_level: int = 1
    is_deleted: bool = False
    created_at: datetime | None = None

    @staticmethod
    def validate_capacity(capacity: int) -> None:
        """Business rule: a PHC must have a positive, bounded capacity."""
        if capacity < MIN_CAPACITY or capacity > MAX_CAPACITY:
            raise ValueError(
                f"capacity must be between {MIN_CAPACITY} and {MAX_CAPACITY}"
            )

    @staticmethod
    def validate_priority_level(priority_level: int) -> None:
        """Business rule: priority level must be within 1..10."""
        if priority_level < 1 or priority_level > 10:
            raise ValueError("priority_level must be between 1 and 10")

    @classmethod
    def create(
        cls,
        name: str,
        code: str,
        district: str,
        state: str,
        latitude: float,
        longitude: float,
        contact: str = "",
        capacity: int = MIN_CAPACITY,
        priority_level: int = 1,
    ) -> "PrimaryHealthCentre":
        if not name or not code or not district or not state:
            raise ValueError("name, code, district and state are required")
        normalized_code = code.strip().upper()
        if not CODE_PATTERN.match(normalized_code):
            raise ValueError(
                "code must contain only letters, digits, dashes or underscores"
            )
        cls.validate_capacity(capacity)
        cls.validate_priority_level(priority_level)
        return cls(
            phc_id=uuid4(),
            name=name.strip(),
            code=normalized_code,
            district=district.strip(),
            state=state.strip(),
            latitude=latitude,
            longitude=longitude,
            contact=contact,
            capacity=capacity,
            priority_level=priority_level,
        )

    def update(
        self,
        name: str | None = None,
        code: str | None = None,
        district: str | None = None,
        state: str | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
        contact: str | None = None,
        capacity: int | None = None,
        priority_level: int | None = None,
    ) -> None:
        """Apply PHC edits; only the provided fields are changed."""
        if name is not None:
            if not name.strip():
                raise ValueError("name is required")
            self.name = name.strip()
        if code is not None:
            normalized_code = code.strip().upper()
            if not CODE_PATTERN.match(normalized_code):
                raise ValueError(
                    "code must contain only letters, digits, dashes or underscores"
                )
            self.code = normalized_code
        if district is not None:
            if not district.strip():
                raise ValueError("district is required")
            self.district = district.strip()
        if state is not None:
            if not state.strip():
                raise ValueError("state is required")
            self.state = state.strip()
        if latitude is not None:
            self.latitude = latitude
        if longitude is not None:
            self.longitude = longitude
        if contact is not None:
            self.contact = contact.strip()
        if capacity is not None:
            self.validate_capacity(capacity)
            self.capacity = capacity
        if priority_level is not None:
            self.validate_priority_level(priority_level)
            self.priority_level = priority_level

    def soft_delete(self) -> None:
        self.is_deleted = True
