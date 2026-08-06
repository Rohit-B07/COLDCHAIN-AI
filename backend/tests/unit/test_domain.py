"""Unit tests for domain value objects and entities (pure logic, no DB)."""

import pytest

from app.domain.entities.shipment import Shipment
from app.domain.value_objects import (
    ExcursionReport,
    GeoCoordinate,
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


class TestShipment:
    def test_create_sets_initial_state(self) -> None:
        shipment = Shipment.create(origin="Delhi", destination="Jaipur")
        assert shipment.status == "created"
        assert shipment.dispatched_at is None

    def test_create_requires_origin_and_destination(self) -> None:
        with pytest.raises(ValueError):
            Shipment.create(origin="", destination="Jaipur")

    def test_dispatch_transitions_state(self) -> None:
        shipment = Shipment.create(origin="Delhi", destination="Jaipur")
        shipment.dispatch()
        assert shipment.status == "dispatched"
        assert shipment.dispatched_at is not None

    def test_cannot_dispatch_twice(self) -> None:
        shipment = Shipment.create(origin="Delhi", destination="Jaipur")
        shipment.dispatch()
        with pytest.raises(ValueError):
            shipment.dispatch()
