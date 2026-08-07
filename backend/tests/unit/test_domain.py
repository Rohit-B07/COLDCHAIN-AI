"""Unit tests for domain value objects and entities (pure logic, no DB)."""

from uuid import uuid4

import pytest

from app.domain.entities.shipment import Shipment
from app.domain.value_objects import (
    ExcursionReport,
    GeoCoordinate,
    ShipmentStatus,
    TemperatureReading,
)


class TestTemperatureReading:
    def test_rejects_below_absolute_zero(self) -> None:
        with pytest.raises(ValueError):
            TemperatureReading(celsius=-300.0, recorded_at="2026-01-01T00:00:00Z")

    def test_accepts_valid_value(self) -> None:
        reading = TemperatureReading(celsius=2.0, recorded_at="2026-01-01T00:00:00Z")
        assert reading.celsius == 2.0


class TestGeoCoordinate:
    def test_rejects_out_of_range_latitude(self) -> None:
        with pytest.raises(ValueError):
            GeoCoordinate(latitude=95.0, longitude=10.0)

    def test_rejects_out_of_range_longitude(self) -> None:
        with pytest.raises(ValueError):
            GeoCoordinate(latitude=10.0, longitude=181.0)

    def test_accepts_valid_coordinates(self) -> None:
        coord = GeoCoordinate(latitude=19.076, longitude=72.8777)
        assert coord.latitude == 19.076


class TestExcursionReport:
    def test_rejects_out_of_range_confidence(self) -> None:
        with pytest.raises(ValueError):
            ExcursionReport(predicted=True, confidence=1.5, risk_level="high")

    def test_rejects_unknown_risk_level(self) -> None:
        with pytest.raises(ValueError):
            ExcursionReport(predicted=True, confidence=0.5, risk_level="critical")


def _shipment(**overrides: object) -> Shipment:
    return Shipment.create(
        tracking_code=overrides.get("tracking_code", "SHP-TEST01"),
        vaccine_name=overrides.get("vaccine_name", "BCG Vaccine"),
        dose_count=overrides.get("dose_count", 100),
        warehouse_id=overrides.get("warehouse_id", uuid4()),
        destination_id=overrides.get("destination_id", uuid4()),
        container_id=overrides.get("container_id"),
        driver_id=overrides.get("driver_id"),
    )


class TestShipment:
    def test_create_sets_initial_state(self) -> None:
        shipment = _shipment()
        assert shipment.status == ShipmentStatus.CREATED
        assert shipment.dispatched_at is None

    def test_create_requires_tracking_code_and_vaccine(self) -> None:
        with pytest.raises(ValueError):
            _shipment(tracking_code="")
        with pytest.raises(ValueError):
            _shipment(vaccine_name="")

    def test_dispatch_transitions_state(self) -> None:
        shipment = _shipment(container_id=uuid4(), driver_id=uuid4())
        shipment.dispatch()
        assert shipment.status == ShipmentStatus.DISPATCHED
        assert shipment.dispatched_at is not None

    def test_cannot_dispatch_twice(self) -> None:
        shipment = _shipment(container_id=uuid4(), driver_id=uuid4())
        shipment.dispatch()
        with pytest.raises(ValueError):
            shipment.dispatch()

    def test_dispatch_requires_container_and_driver(self) -> None:
        with pytest.raises(ValueError):
            _shipment().dispatch()
