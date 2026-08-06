"""Domain entities for facilities (warehouse / primary health centre)."""

from dataclasses import dataclass
from uuid import UUID, uuid4


@dataclass
class Warehouse:
    warehouse_id: UUID
    name: str
    code: str
    latitude: float
    longitude: float
    address: str = ""
    capacity: int = 0

    @classmethod
    def create(
        cls,
        name: str,
        code: str,
        latitude: float,
        longitude: float,
        address: str = "",
        capacity: int = 0,
    ) -> "Warehouse":
        if not name or not code:
            raise ValueError("name and code are required")
        return cls(
            warehouse_id=uuid4(),
            name=name.strip(),
            code=code.strip().upper(),
            latitude=latitude,
            longitude=longitude,
            address=address,
            capacity=capacity,
        )


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
    capacity: int = 0
    priority_level: int = 1

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
        capacity: int = 0,
        priority_level: int = 1,
    ) -> "PrimaryHealthCentre":
        if not name or not code or not district or not state:
            raise ValueError("name, code, district and state are required")
        return cls(
            phc_id=uuid4(),
            name=name.strip(),
            code=code.strip().upper(),
            district=district.strip(),
            state=state.strip(),
            latitude=latitude,
            longitude=longitude,
            contact=contact,
            capacity=capacity,
            priority_level=priority_level,
        )
