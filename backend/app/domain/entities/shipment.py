"""Domain entity: Shipment.

A shipment is the core aggregate: a cold-chain delivery of a vaccine batch from
a warehouse (origin) to a primary health centre (destination), carried in a
temperature-controlled container.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.domain.value_objects import Priority, ShipmentStatus


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
        if dose_count < 0:
            raise ValueError("dose_count must be non-negative")
        if temperature_min >= temperature_max:
            raise ValueError("temperature_min must be less than temperature_max")
        return cls(
            shipment_id=uuid4(),
            tracking_code=tracking_code.strip().upper(),
            vaccine_name=vaccine_name.strip(),
            dose_count=dose_count,
            warehouse_id=warehouse_id,
            destination_id=destination_id,
            container_id=container_id,
            driver_id=driver_id,
            temperature_min=temperature_min,
            temperature_max=temperature_max,
        )

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

    def deliver(self, at: datetime | None = None) -> None:
        if self.status is not ShipmentStatus.IN_TRANSIT:
            raise ValueError(f"Cannot deliver shipment in {self.status.name!r}")
        self.status = ShipmentStatus.DELIVERED
        self.delivered_at = at or datetime.now(UTC)