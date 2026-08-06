"""Domain entities for logistics assets: drivers, vehicles, cold containers."""

from dataclasses import dataclass
from uuid import UUID, uuid4


@dataclass
class Driver:
    driver_id: UUID
    name: str
    phone: str
    license_number: str
    status: str = "available"
    vehicle_id: UUID | None = None

    @classmethod
    def create(
        cls, name: str, phone: str, license_number: str, vehicle_id: UUID | None = None
    ) -> "Driver":
        if not name or not phone or not license_number:
            raise ValueError("name, phone and license_number are required")
        return cls(
            driver_id=uuid4(),
            name=name.strip(),
            phone=phone.strip(),
            license_number=license_number.strip(),
            vehicle_id=vehicle_id,
        )


@dataclass
class Vehicle:
    vehicle_id: UUID
    registration_number: str
    vehicle_type: str = "refrigerated_van"
    capacity_kg: int = 500
    is_reefer: bool = True
    status: str = "active"

    @classmethod
    def create(
        cls,
        registration_number: str,
        vehicle_type: str = "refrigerated_van",
        capacity_kg: int = 500,
        is_reefer: bool = True,
    ) -> "Vehicle":
        if not registration_number:
            raise ValueError("registration_number is required")
        return cls(
            vehicle_id=uuid4(),
            registration_number=registration_number.strip().upper(),
            vehicle_type=vehicle_type,
            capacity_kg=capacity_kg,
            is_reefer=is_reefer,
        )


@dataclass
class ColdContainer:
    container_id: UUID
    asset_tag: str
    temperature_setpoint: float = 4.0
    min_temperature: float = 2.0
    max_temperature: float = 8.0
    status: str = "idle"
    current_latitude: float | None = None
    current_longitude: float | None = None
    battery_level: int = 100

    @classmethod
    def create(
        cls,
        asset_tag: str,
        temperature_setpoint: float = 4.0,
        min_temperature: float = 2.0,
        max_temperature: float = 8.0,
    ) -> "ColdContainer":
        if not asset_tag:
            raise ValueError("asset_tag is required")
        if not min_temperature <= temperature_setpoint <= max_temperature:
            raise ValueError("setpoint must lie within the safe temperature band")
        return cls(
            container_id=uuid4(),
            asset_tag=asset_tag.strip().upper(),
            temperature_setpoint=temperature_setpoint,
            min_temperature=min_temperature,
            max_temperature=max_temperature,
        )
