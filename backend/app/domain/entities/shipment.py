"""Domain entity: Shipment.

A shipment is the core aggregate: a cold-chain delivery of a vaccine batch from
a warehouse (origin) to a primary health centre (destination), carried in a
temperature-controlled container.
"""

import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.domain.value_objects import Priority, ShipmentStatus

TRACKING_CODE_PREFIX = "SHP"
TRACKING_CODE_PATTERN = re.compile(r"^SHP-[A-Z0-9]{4,32}$")
MIN_DOSE_COUNT = 1
MAX_DOSE_COUNT = 1_000_000
MIN_TEMPERATURE = -80.0
MAX_TEMPERATURE = 60.0
EDITABLE_STATUSES = {ShipmentStatus.CREATED, ShipmentStatus.PREDICTED}


@dataclass
class Shipment:
    """A cold-chain delivery shipment."""

    shipment_id: UUID
    tracking_code: str
    vaccine_name: str
    dose_count: int
    priority: Priority
    temperature_min: float
    temperature_max: float
    warehouse_id: UUID
    destination_id: UUID
    container_id: UUID | None
    driver_id: UUID | None
    status: ShipmentStatus = ShipmentStatus.CREATED
    dispatched_at: datetime | None = None
    delivered_at: datetime | None = None
    estimated_delivery_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    is_deleted: bool = False
    deleted_at: datetime | None = None

    @staticmethod
    def validate_dose_count(dose_count: int) -> None:
        """Business rule: a shipment must carry a positive, bounded dose count."""
        if dose_count < MIN_DOSE_COUNT or dose_count > MAX_DOSE_COUNT:
            raise ValueError(
                f"dose_count must be between {MIN_DOSE_COUNT} and {MAX_DOSE_COUNT}"
            )

    @staticmethod
    def validate_temperature(temperature_min: float, temperature_max: float) -> None:
        """Business rule: the safe band must be within cold-chain bounds."""
        if temperature_min < MIN_TEMPERATURE or temperature_max > MAX_TEMPERATURE:
            raise ValueError(
                f"temperature must be between {MIN_TEMPERATURE} and {MAX_TEMPERATURE}"
            )
        if temperature_min >= temperature_max:
            raise ValueError("temperature_min must be less than temperature_max")

    @classmethod
    def generate_tracking_code(cls) -> str:
        """Generate a unique, human-readable tracking code."""
        return f"{TRACKING_CODE_PREFIX}-{uuid4().hex[:10].upper()}"

    @classmethod
    def create(
        cls,
        tracking_code: str,
        vaccine_name: str,
        dose_count: int,
        warehouse_id: UUID,
        destination_id: UUID,
        priority: Priority | str = Priority.MEDIUM,
        temperature_min: float = 2.0,
        temperature_max: float = 8.0,
        container_id: UUID | None = None,
        driver_id: UUID | None = None,
    ) -> "Shipment":
        if not tracking_code or not vaccine_name:
            raise ValueError("tracking_code and vaccine_name are required")
        normalized_code = tracking_code.strip().upper()
        if not TRACKING_CODE_PATTERN.match(normalized_code):
            raise ValueError(
                f"tracking_code must match {TRACKING_CODE_PATTERN.pattern}"
            )
        if isinstance(priority, str):
            priority = Priority(priority)
        cls.validate_dose_count(dose_count)
        cls.validate_temperature(temperature_min, temperature_max)
        return cls(
            shipment_id=uuid4(),
            tracking_code=normalized_code,
            vaccine_name=vaccine_name.strip(),
            dose_count=dose_count,
            warehouse_id=warehouse_id,
            destination_id=destination_id,
            container_id=container_id,
            driver_id=driver_id,
            priority=priority,
            temperature_min=temperature_min,
            temperature_max=temperature_max,
        )

    def update(
        self,
        vaccine_name: str | None = None,
        dose_count: int | None = None,
        priority: Priority | str | None = None,
        temperature_min: float | None = None,
        temperature_max: float | None = None,
        container_id: UUID | None = None,
        driver_id: UUID | None = None,
        estimated_delivery_at: datetime | None = None,
    ) -> None:
        """Apply shipment edits; only dispatched shipments are locked."""
        if self.status not in EDITABLE_STATUSES:
            raise ValueError(
                f"cannot edit a shipment in state {self.status.value!r}"
            )
        if vaccine_name is not None:
            if not vaccine_name.strip():
                raise ValueError("vaccine_name is required")
            self.vaccine_name = vaccine_name.strip()
        if dose_count is not None:
            self.validate_dose_count(dose_count)
            self.dose_count = dose_count
        if priority is not None:
            if isinstance(priority, str):
                priority = Priority(priority)
            self.priority = priority
        if temperature_min is not None or temperature_max is not None:
            new_min = temperature_min if temperature_min is not None else self.temperature_min
            new_max = temperature_max if temperature_max is not None else self.temperature_max
            self.validate_temperature(new_min, new_max)
            self.temperature_min = new_min
            self.temperature_max = new_max
        if container_id is not None:
            self.container_id = container_id
        if driver_id is not None:
            self.driver_id = driver_id
        if estimated_delivery_at is not None:
            self.estimated_delivery_at = estimated_delivery_at

    def dispatch(self, at: datetime | None = None) -> None:
        if self.status not in {ShipmentStatus.CREATED, ShipmentStatus.PREDICTED}:
            raise ValueError(f"Cannot dispatch shipment in state {self.status.value!r}")
        if self.container_id is None or self.driver_id is None:
            raise ValueError("shipment must have a container and a driver before dispatch")
        self.status = ShipmentStatus.DISPATCHED
        self.dispatched_at = at or datetime.now(UTC)

    def mark_predicted(self) -> None:
        if self.status in {ShipmentStatus.DISPATCHED, ShipmentStatus.IN_TRANSIT}:
            return
        self.status = ShipmentStatus.PREDICTED

    def cancel(self) -> None:
        if self.status not in EDITABLE_STATUSES:
            raise ValueError(
                f"Cannot cancel shipment in state {self.status.value!r}"
            )
        self.status = ShipmentStatus.CANCELLED

    def deliver(self, at: datetime | None = None) -> None:
        if self.status is not ShipmentStatus.IN_TRANSIT:
            raise ValueError(f"Cannot deliver shipment in {self.status.name!r}")
        self.status = ShipmentStatus.DELIVERED
        self.delivered_at = at or datetime.now(UTC)

    def soft_delete(self) -> None:
        self.is_deleted = True
        self.deleted_at = datetime.now(UTC)
