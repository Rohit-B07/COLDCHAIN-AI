"""API tests for the analytics dashboard endpoint (no live DB).

The route and aggregation service are exercised against in-memory fake
repositories by overriding the service and role dependencies. A separate test
hits the real application to assert the endpoint is protected.
"""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.deps.container import get_analytics_service
from app.api.deps.rbac import get_user_roles
from app.api.errors import register_exception_handlers
from app.api.routes import api_router
from app.core.config import get_settings
from app.core.rbac import Role
from app.domain.entities.intelligence import ColdAlert, Prediction
from app.domain.entities.shipment import Shipment
from app.domain.value_objects import ShipmentStatus
from app.main import app as real_app
from app.services.analytics_service import AnalyticsService


def _shipment(
    *,
    status: ShipmentStatus = ShipmentStatus.CREATED,
    estimated_delivery_at: datetime | None = None,
) -> Shipment:
    shipment = Shipment.create(
        tracking_code="SHP-ABC123",
        vaccine_name="BCG Vaccine",
        dose_count=100,
        warehouse_id=uuid4(),
        destination_id=uuid4(),
    )
    shipment.status = status
    shipment.estimated_delivery_at = estimated_delivery_at
    return shipment


def _prediction(
    *,
    risk_level: str,
    min_temp: float,
    max_temp: float,
) -> Prediction:
    return Prediction(
        prediction_id=uuid4(),
        shipment_id=uuid4(),
        excursion_risk=0.5,
        risk_level=risk_level,
        confidence=0.9,
        expected_min_temp=min_temp,
        expected_max_temp=max_temp,
        model_version="rule-based-v1",
        features={},
        explanations={},
        created_at=datetime.now(UTC),
    )


def _alert(*, severity: str, status: str) -> ColdAlert:
    return ColdAlert(
        alert_id=uuid4(),
        severity=severity,
        alert_type="temperature_excursion",
        message="Container temperature above safe band",
        shipment_id=uuid4(),
        status=status,
        created_at=datetime.now(UTC),
    )


class _FakeShipmentRepo:
    def __init__(self, shipments: list[Shipment]) -> None:
        self._items = list(shipments)

    async def list(self) -> list[Shipment]:
        return list(self._items)


class _FakePredictionRepo:
    def __init__(self, predictions: list[Prediction]) -> None:
        self._items = list(predictions)

    async def count(
        self,
        *,
        shipment_id=None,
        risk_level: str | None = None,
        model_version: str | None = None,
    ) -> int:
        if risk_level is None:
            return len(self._items)
        return sum(1 for p in self._items if p.risk_level == risk_level)

    async def list_paginated(
        self,
        *,
        shipment_id=None,
        risk_level: str | None = None,
        model_version: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Prediction]:
        return self._items[offset : offset + limit]


class _FakeAlertRepo:
    def __init__(self, alerts: list[ColdAlert]) -> None:
        self._items = list(alerts)

    async def count(
        self,
        *,
        shipment_id=None,
        container_id=None,
        severity: str | None = None,
        status: str | None = None,
    ) -> int:
        if status is None:
            return len(self._items)
        return sum(1 for a in self._items if a.status == status)


class _FakeNotificationService:
    def __init__(self, total: int, unread: int) -> None:
        self._total = total
        self._unread = unread

    async def counts(self) -> tuple[int, int]:
        return self._total, self._unread


def _service(
    *,
    shipments: list[Shipment],
    predictions: list[Prediction],
    alerts: list[ColdAlert],
    notification_total: int = 0,
    notification_unread: int = 0,
) -> AnalyticsService:
    return AnalyticsService(
        shipment_repo=_FakeShipmentRepo(shipments),
        prediction_repo=_FakePredictionRepo(predictions),
        alert_repo=_FakeAlertRepo(alerts),
        notification_service=_FakeNotificationService(
            notification_total, notification_unread
        ),
    )


def _test_app(service: AnalyticsService) -> FastAPI:
    settings = get_settings()
    application = FastAPI()
    application.include_router(api_router, prefix=settings.API_V1_STR)
    register_exception_handlers(application)
    application.dependency_overrides[get_user_roles] = lambda: frozenset({Role.ADMIN})
    application.dependency_overrides[get_analytics_service] = lambda: service
    return application


def test_analytics_requires_authentication() -> None:
    response = TestClient(real_app).get("/api/v1/analytics/dashboard")
    assert response.status_code == 401


def test_analytics_empty_data() -> None:
    app = _test_app(_service(shipments=[], predictions=[], alerts=[]))
    response = TestClient(app).get("/api/v1/analytics/dashboard")
    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["shipments"] == {
        "total": 0,
        "active": 0,
        "completed": 0,
        "delayed": 0,
    }
    assert payload["predictions"] == {
        "total": 0,
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
    }
    assert payload["alerts"] == {"open": 0, "resolved": 0}
    assert payload["notifications"] == {"unread": 0, "total": 0}
    assert payload["temperature"] == {"average": 0.0, "maximum": 0.0, "minimum": 0.0}


def test_analytics_realistic_counts() -> None:
    now = datetime.now(UTC)
    shipments = [
        _shipment(status=ShipmentStatus.CREATED),
        _shipment(
            status=ShipmentStatus.IN_TRANSIT,
            estimated_delivery_at=now - timedelta(hours=2),
        ),
        _shipment(
            status=ShipmentStatus.IN_TRANSIT,
            estimated_delivery_at=now + timedelta(hours=2),
        ),
        _shipment(status=ShipmentStatus.DISPATCHED),
        _shipment(status=ShipmentStatus.DELIVERED),
        _shipment(status=ShipmentStatus.PREDICTED),
    ]
    predictions = [
        _prediction(risk_level="critical", min_temp=2.0, max_temp=8.0),
        _prediction(risk_level="critical", min_temp=2.0, max_temp=8.0),
        _prediction(risk_level="high", min_temp=0.0, max_temp=4.0),
        _prediction(risk_level="medium", min_temp=2.0, max_temp=6.0),
        _prediction(risk_level="low", min_temp=4.0, max_temp=10.0),
    ]
    alerts = [
        _alert(severity="critical", status="open"),
        _alert(severity="warning", status="open"),
        _alert(severity="info", status="resolved"),
    ]
    app = _test_app(
        _service(
            shipments=shipments,
            predictions=predictions,
            alerts=alerts,
            notification_total=8,
            notification_unread=5,
        )
    )
    response = TestClient(app).get("/api/v1/analytics/dashboard")
    assert response.status_code == 200
    payload = response.json()["data"]

    assert payload["shipments"]["total"] == 6
    assert payload["shipments"]["active"] == 4
    assert payload["shipments"]["completed"] == 1
    assert payload["shipments"]["delayed"] == 1

    assert payload["predictions"]["total"] == 5
    assert payload["predictions"]["critical"] == 2
    assert payload["predictions"]["high"] == 1
    assert payload["predictions"]["medium"] == 1
    assert payload["predictions"]["low"] == 1

    assert payload["alerts"]["open"] == 2
    assert payload["alerts"]["resolved"] == 1

    assert payload["notifications"]["total"] == 8
    assert payload["notifications"]["unread"] == 5

    assert payload["temperature"] == {"average": 4.6, "maximum": 10.0, "minimum": 0.0}
