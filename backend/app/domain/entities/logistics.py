"""Domain entities for logistics assets: drivers, vehicles, cold containers."""

import re
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4

DRIVER_STATUSES = ("available", "assigned", "on_leave")
PHONE_PATTERN = re.compile(r"^\+?[1-9]\d{9,13}$")
LICENSE_PATTERN = re.compile(r"^[A-Z0-9][A-Z0-9-]{5,31}$")

MIN_CAPACITY_KG = 1
MAX_CAPACITY_KG = 50_000
VEHICLE_STATUSES = ("active", "maintenance", "retired")
MAINTENANCE_STATUSES = ("ok", "scheduled", "in_progress", "overdue")
VEHICLE_TYPES = ("refrigerated_van", "refrigerated_truck", "motorcycle_cooler")
REEFER_TYPES = ("refrigerated_van", "refrigerated_truck")


@dataclass
class Driver:
    driver_id: UUID
    name: str
    phone: str
    license_number: str
    status: str = "available"
    vehicle_id: UUID | None = None
    is_deleted: bool = False
    created_at: datetime | None = None

    @staticmethod
    def normalize_phone(phone: str) -> str:
        return re.sub(r"[\s\-().]", "", phone.strip())

    @staticmethod
    def validate_phone(phone: str) -> None:
        """Business rule: phone must be a 10-15 digit number (optional leading +)."""
        if not PHONE_PATTERN.match(phone):
            raise ValueError(
                "phone must be a valid number: 10-15 digits with optional leading +"
            )

    @staticmethod
    def normalize_license(license_number: str) -> str:
        return re.sub(r"\s+", "", license_number.strip()).upper()

    @staticmethod
    def validate_license(license_number: str) -> None:
        """Business rule: license must be 6-32 alphanumeric chars, hyphen allowed."""
        if not LICENSE_PATTERN.match(license_number):
            raise ValueError(
                "license_number must contain only letters, digits or hyphens "
                "(6-32 characters)"
            )

    @classmethod
    def create(
        cls, name: str, phone: str, license_number: str, vehicle_id: UUID | None = None
    ) -> "Driver":
        if not name or not phone or not license_number:
            raise ValueError("name, phone and license_number are required")
        normalized_phone = cls.normalize_phone(phone)
        normalized_license = cls.normalize_license(license_number)
        cls.validate_phone(normalized_phone)
        cls.validate_license(normalized_license)
        return cls(
            driver_id=uuid4(),
            name=name.strip(),
            phone=normalized_phone,
            license_number=normalized_license,
            status="assigned" if vehicle_id is not None else "available",
            vehicle_id=vehicle_id,
        )

    def update(
        self,
        name: str | None = None,
        phone: str | None = None,
        license_number: str | None = None,
    ) -> None:
        """Apply driver edits; only the provided fields are changed."""
        if name is not None:
            if not name.strip():
                raise ValueError("name is required")
            self.name = name.strip()
        if phone is not None:
            normalized_phone = self.normalize_phone(phone)
            self.validate_phone(normalized_phone)
            self.phone = normalized_phone
        if license_number is not None:
            normalized_license = self.normalize_license(license_number)
            self.validate_license(normalized_license)
            self.license_number = normalized_license

    def change_status(self, status: str) -> None:
        """Transition driver status, keeping it consistent with assignments."""
        normalized = status.strip().lower()
        if normalized not in DRIVER_STATUSES:
            raise ValueError(f"status must be one of {', '.join(DRIVER_STATUSES)}")
        if normalized == "assigned" and self.vehicle_id is None:
            raise ValueError("cannot mark a driver as assigned without a vehicle")
        if normalized != "assigned" and self.vehicle_id is not None:
            raise ValueError("unassign the vehicle before changing status")
        self.status = normalized

    def assign_vehicle(self, vehicle_id: UUID) -> None:
        """Assign this driver to a vehicle; on-leave drivers cannot be assigned."""
        if self.status == "on_leave":
            raise ValueError("cannot assign a driver on leave")
        self.vehicle_id = vehicle_id
        self.status = "assigned"

    def unassign_vehicle(self) -> None:
        self.vehicle_id = None
        if self.status == "assigned":
            self.status = "available"

    def soft_delete(self) -> None:
        self.is_deleted = True


@dataclass
class Vehicle:
    vehicle_id: UUID
    registration_number: str
    vehicle_type: str = "refrigerated_van"
    capacity_kg: int = 500
    is_reefer: bool = True
    status: str = "active"
    maintenance_status: str = "ok"
    last_maintenance_at: datetime | None = None
    next_maintenance_due_at: datetime | None = None
    is_deleted: bool = False
    created_at: datetime | None = None

    @staticmethod
    def validate_capacity(capacity_kg: int) -> None:
        """Business rule: payload capacity must be positive and bounded."""
        if capacity_kg < MIN_CAPACITY_KG or capacity_kg > MAX_CAPACITY_KG:
            raise ValueError(
                f"capacity_kg must be between {MIN_CAPACITY_KG} and {MAX_CAPACITY_KG}"
            )

    @staticmethod
    def validate_type(vehicle_type: str) -> None:
        """Business rule: vehicle type must be one of the supported classes."""
        if vehicle_type not in VEHICLE_TYPES:
            raise ValueError(f"vehicle_type must be one of {', '.join(VEHICLE_TYPES)}")

    @staticmethod
    def validate_cold_storage(vehicle_type: str, is_reefer: bool) -> None:
        """Business rule: refrigerated types must carry a refrigeration unit."""
        if vehicle_type in REEFER_TYPES and not is_reefer:
            raise ValueError(
                "refrigerated vehicles must be marked as reefers (is_reefer=True)"
            )

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
        normalized = registration_number.strip().upper()
        cls.validate_type(vehicle_type)
        cls.validate_capacity(capacity_kg)
        cls.validate_cold_storage(vehicle_type, is_reefer)
        return cls(
            vehicle_id=uuid4(),
            registration_number=normalized,
            vehicle_type=vehicle_type,
            capacity_kg=capacity_kg,
            is_reefer=is_reefer,
        )

    def update(
        self,
        registration_number: str | None = None,
        vehicle_type: str | None = None,
        capacity_kg: int | None = None,
        is_reefer: bool | None = None,
    ) -> None:
        """Apply vehicle edits; only the provided fields are changed."""
        if registration_number is not None:
            if not registration_number.strip():
                raise ValueError("registration_number is required")
            self.registration_number = registration_number.strip().upper()
        if vehicle_type is not None:
            self.validate_type(vehicle_type)
            self.vehicle_type = vehicle_type
        if capacity_kg is not None:
            self.validate_capacity(capacity_kg)
            self.capacity_kg = capacity_kg
        if is_reefer is not None:
            self.is_reefer = is_reefer
        if vehicle_type is not None or is_reefer is not None:
            self.validate_cold_storage(self.vehicle_type, self.is_reefer)

    def change_status(self, status: str) -> None:
        """Transition vehicle status, keeping maintenance state consistent."""
        normalized = status.strip().lower()
        if normalized not in VEHICLE_STATUSES:
            raise ValueError(f"status must be one of {', '.join(VEHICLE_STATUSES)}")
        if self.status == "retired" and normalized != "retired":
            raise ValueError("cannot reactivate a retired vehicle")
        if normalized == "maintenance":
            self.maintenance_status = "in_progress"
        elif normalized == "active":
            self.maintenance_status = "ok"
        self.status = normalized

    def set_maintenance_status(self, maintenance_status: str) -> None:
        """Update maintenance status, respecting vehicle state invariants."""
        normalized = maintenance_status.strip().lower()
        if normalized not in MAINTENANCE_STATUSES:
            raise ValueError(
                f"maintenance_status must be one of {', '.join(MAINTENANCE_STATUSES)}"
            )
        if self.status == "retired":
            raise ValueError("cannot set maintenance status on a retired vehicle")
        if normalized == "in_progress" and self.status != "maintenance":
            raise ValueError(
                "vehicle must be in maintenance status to mark maintenance in progress"
            )
        self.maintenance_status = normalized

    def soft_delete(self) -> None:
        self.is_deleted = True


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
