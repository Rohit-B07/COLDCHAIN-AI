"""API tests for the notification feed endpoint (no live DB).

The behavioural tests exercise the route and the aggregation service against
in-memory fake repositories by overriding the service and role dependencies.
A separate test hits the real application to assert the endpoint is protected.
"""

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.deps.container import get_notification_service
from app.api.deps.rbac import get_user_roles
from app.api.errors import register_exception_handlers
from app.api.routes import api_router
from app.core.config import get_settings
from app.core.rbac import Role
from app.domain.entities.intelligence import ColdAlert, Prediction
from app.domain.entities.shipment import Shipment
from app.main import app as real_app
from app.services.notification_service import NotificationService


def _prediction(
    *,
    risk_level: str = "high",
    created_at: datetime,
    shipment_id: UUID | None = None,
) -> Prediction:
    return Prediction(
        prediction_id=uuid4(),
        shipment_id=shipment_id or uuid4(),
        excursion_risk=0.8,
        risk_level=risk_level,
        confidence=0.9,
        expected_min_temp=2.0,
        expected_max_temp=8.0,
        model_version="rule-based-v1",
        features={"risk_score": 0.8},
        explanations={
            "model": "rule-based-v1",
            "rules": [
                {
                    "name": "ambient_temperature_delta",
                    "contribution": 0.2,
                    "detail": "ambient deviates 3.2°C from the safe band",
                }
            ],
        },
        created_at=created_at,
    )


def _alert(
    *,
    severity: str = "warning",
    status: str = "open",
    created_at: datetime,
) -> ColdAlert:
    return ColdAlert(
        alert_id=uuid4(),
        severity=severity,
        alert_type="temperature_excursion",
        message="Container temperature above safe band",
        shipment_id=uuid4(),
        status=status,
        created_at=created_at,
    )


def _shipment(created_at: datetime) -> Shipment:
    shipment = Shipment.create(
        tracking_code="SHP-ABC123",
        vaccine_name="BCG Vaccine",
        dose_count=100,
        warehouse_id=uuid4(),
        destination_id=uuid4(),
    )
    shipment.created_at = created_at
    return shipment


class _FakePredictionRepo:
    def __init__(self, predictions: list[Prediction]) -> None:
        self._items = list(predictions)

    async def count(
        self,
        *,
        shipment_id: UUID | None = None,
        risk_level: str | None = None,
        model_version: str | None = None,
    ) -> int:
        return len(self._items)

    async def list_paginated(
        self,
        *,
        shipment_id: UUID | None = None,
        risk_level: str | None = None,
        model_version: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Prediction]:
        items = sorted(
            self._items,
            key=lambda p: p.created_at or datetime.min(UTC),
            reverse=True,
        )
        return items[offset : offset + limit]


class _FakeAlertRepo:
    def __init__(self, alerts: list[ColdAlert]) -> None:
        self._items = list(alerts)

    async def count(
        self,
        *,
        shipment_id: UUID | None = None,
        container_id: UUID | None = None,
        severity: str | None = None,
        status: str | None = None,
    ) -> int:
        return len(self._filter(status=status))

    async def list_paginated(
        self,
        *,
        shipment_id: UUID | None = None,
        container_id: UUID | None = None,
        severity: str | None = None,
        status: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> list[ColdAlert]:
        items = sorted(
            self._filter(status=status),
            key=lambda a: a.created_at or datetime.min(UTC),
            reverse=True,
        )
        return items[offset : offset + limit]

    def _filter(self, *, status: str | None) -> list[ColdAlert]:
        if status is None:
            return list(self._items)
        return [a for a in self._items if a.status == status]


class _FakeShipmentRepo:
    def __init__(self, shipments: list[Shipment]) -> None:
        self._items = list(shipments)

    async def count(
        self,
        *,
        search: str | None = None,
        status: str | None = None,
        priority: str | None = None,
    ) -> int:
        return len(self._items)

    async def list_paginated(
        self,
        *,
        search: str | None = None,
        status: str | None = None,
        priority: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Shipment]:
        items = sorted(
            self._items,
            key=lambda s: s.created_at or datetime.min(UTC),
            reverse=True,
        )
        return items[offset : offset + limit]


def _service(
    *,
    predictions: list[Prediction],
    alerts: list[ColdAlert],
    shipments: list[Shipment],
) -> NotificationService:
    return NotificationService(
        prediction_repo=_FakePredictionRepo(predictions),
        alert_repo=_FakeAlertRepo(alerts),
        shipment_repo=_FakeShipmentRepo(shipments),
    )


def _test_app(service: NotificationService) -> FastAPI:
    settings = get_settings()
    application = FastAPI()
    application.include_router(api_router, prefix=settings.API_V1_STR)
    register_exception_handlers(application)
    application.dependency_overrides[get_user_roles] = lambda: frozenset({Role.ADMIN})
    application.dependency_overrides[get_notification_service] = lambda: service
    return application


def test_notifications_requires_authentication() -> None:
    response = TestClient(real_app).get("/api/v1/notifications")
    assert response.status_code == 401


def test_notifications_empty_feed() -> None:
    app = _test_app(_service(predictions=[], alerts=[], shipments=[]))
    response = TestClient(app).get("/api/v1/notifications")
    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["items"] == []
    assert payload["total"] == 0
    assert payload["unread_count"] == 0
    assert payload["pages"] == 0
    assert payload["page"] == 1
    assert payload["size"] == 20


def test_notifications_mixed_feed_newest_first() -> None:
    now = datetime.now(UTC)
    prediction = _prediction(risk_level="high", created_at=now - timedelta(hours=3))
    acknowledged = _alert(status="acknowledged", created_at=now - timedelta(hours=5))
    shipment = _shipment(now - timedelta(hours=8))
    open_alert = _alert(
        severity="critical", status="open", created_at=now - timedelta(hours=10)
    )

    app = _test_app(
        _service(
            predictions=[prediction],
            alerts=[acknowledged, open_alert],
            shipments=[shipment],
        )
    )
    response = TestClient(app).get("/api/v1/notifications")
    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["total"] == 4
    assert payload["unread_count"] == 3
    assert [item["type"] for item in payload["items"]] == [
        "prediction",
        "alert",
        "shipment",
        "alert",
    ]

    first = payload["items"][0]
    assert first["title"] == "Excursion risk: high"
    assert first["severity"] == "critical"
    assert first["read"] is False
    assert first["prediction_id"] == str(prediction.prediction_id)
    assert first["shipment_id"] == str(prediction.shipment_id)
    assert first["message"] == "ambient deviates 3.2°C from the safe band"

    assert payload["items"][1]["read"] is True
    assert payload["items"][2]["type"] == "shipment"
    assert payload["items"][2]["severity"] == "info"
    assert "SHP-ABC123" in payload["items"][2]["message"]
    assert payload["items"][3]["read"] is False
    assert payload["items"][3]["severity"] == "critical"


def test_notifications_unread_only() -> None:
    now = datetime.now(UTC)
    app = _test_app(
        _service(
            predictions=[
                _prediction(risk_level="medium", created_at=now - timedelta(hours=1))
            ],
            alerts=[
                _alert(status="acknowledged", created_at=now - timedelta(hours=2)),
                _alert(status="open", created_at=now - timedelta(hours=3)),
            ],
            shipments=[_shipment(now - timedelta(hours=4))],
        )
    )
    response = TestClient(app).get("/api/v1/notifications?unread_only=true")
    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["total"] == 3
    assert payload["unread_count"] == 3
    assert len(payload["items"]) == 3
    assert all(item["read"] is False for item in payload["items"])


def test_notifications_paginates() -> None:
    now = datetime.now(UTC)
    shipments = [_shipment(now - timedelta(hours=i)) for i in range(5)]
    app = _test_app(_service(predictions=[], alerts=[], shipments=shipments))
    page_one = TestClient(app).get("/api/v1/notifications?page=1&size=2")
    page_one_payload = page_one.json()["data"]
    assert page_one_payload["total"] == 5
    assert page_one_payload["pages"] == 3
    assert [item["title"] for item in page_one_payload["items"]] == [
        "Shipment SHP-ABC123",
        "Shipment SHP-ABC123",
    ]
    page_two = TestClient(app).get("/api/v1/notifications?page=2&size=2")
    assert len(page_two.json()["data"]["items"]) == 2
