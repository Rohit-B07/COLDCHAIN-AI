"""API tests for the prediction-history endpoint (no live DB).

The RBAC middleware and route-level permission dependency are both bypassed in
the behavioural tests by overriding the service and role dependencies, so the
route logic (pagination, filtering, presentation mapping) is exercised against
in-memory fakes. A separate test hits the real application to assert that the
endpoint is protected and rejects unauthenticated callers.
"""

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.deps.container import get_prediction_history_service
from app.api.deps.rbac import get_user_roles
from app.api.errors import register_exception_handlers
from app.api.routes import api_router
from app.core.config import get_settings
from app.core.rbac import Role
from app.domain.entities.intelligence import Prediction
from app.main import app as real_app
from app.services.prediction_history_service import PredictionHistoryService
from app.services.prediction_service import PredictionService


def _make_prediction(
    *,
    shipment_id: UUID | None = None,
    risk_level: str = "medium",
    risk_score: float = 0.5,
    created_at: datetime | None = None,
) -> Prediction:
    return Prediction(
        prediction_id=uuid4(),
        shipment_id=shipment_id or uuid4(),
        excursion_risk=risk_score,
        risk_level=risk_level,
        confidence=0.9,
        expected_min_temp=2.0,
        expected_max_temp=8.0,
        model_version="rule-based-v1",
        features={"risk_score": risk_score},
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
        created_at=created_at or datetime.now(UTC),
    )


class _FakePredictionRepo:
    def __init__(self, predictions: list[Prediction]) -> None:
        self._items = list(predictions)

    async def list_paginated(
        self,
        *,
        shipment_id: UUID | None = None,
        risk_level: str | None = None,
        model_version: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Prediction]:
        items = self._filter(shipment_id=shipment_id, risk_level=risk_level)
        return items[offset : offset + limit]

    async def count(
        self,
        *,
        shipment_id: UUID | None = None,
        risk_level: str | None = None,
        model_version: str | None = None,
    ) -> int:
        return len(self._filter(shipment_id=shipment_id, risk_level=risk_level))

    def _filter(
        self, *, shipment_id: UUID | None, risk_level: str | None
    ) -> list[Prediction]:
        items = [
            p
            for p in self._items
            if (shipment_id is None or p.shipment_id == shipment_id)
            and (risk_level is None or p.risk_level == risk_level)
        ]
        items.sort(
            key=lambda p: p.created_at or datetime.min(UTC),
            reverse=True,
        )
        return items


class _FakeShipmentRepo:
    async def get(self, shipment_id: UUID) -> None:
        return None


def _history_service(predictions: list[Prediction]) -> PredictionHistoryService:
    prediction_service = PredictionService(
        prediction_repo=_FakePredictionRepo(predictions),
        shipment_repo=_FakeShipmentRepo(),
    )
    return PredictionHistoryService(prediction_service=prediction_service)


def _test_app(history_service: PredictionHistoryService) -> FastAPI:
    settings = get_settings()
    application = FastAPI()
    application.include_router(api_router, prefix=settings.API_V1_STR)
    register_exception_handlers(application)
    application.dependency_overrides[get_user_roles] = lambda: frozenset({Role.ADMIN})
    application.dependency_overrides[get_prediction_history_service] = (
        lambda: history_service
    )
    return application


def test_history_requires_authentication() -> None:
    response = TestClient(real_app).get("/api/v1/predictions/history")
    assert response.status_code == 401


def test_history_returns_empty_page() -> None:
    response = TestClient(_test_app(_history_service([]))).get(
        "/api/v1/predictions/history"
    )
    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["items"] == []
    assert payload["total"] == 0
    assert payload["page"] == 1
    assert payload["size"] == 20
    assert payload["pages"] == 0


def test_history_returns_items_newest_first() -> None:
    older = _make_prediction(
        risk_level="low",
        risk_score=0.2,
        created_at=datetime.now(UTC) - timedelta(hours=2),
    )
    newer = _make_prediction(
        risk_level="high",
        risk_score=0.9,
        created_at=datetime.now(UTC),
    )
    response = TestClient(_test_app(_history_service([older, newer]))).get(
        "/api/v1/predictions/history"
    )
    assert response.status_code == 200
    items = response.json()["data"]["items"]
    assert [item["id"] for item in items] == [
        str(newer.prediction_id),
        str(older.prediction_id),
    ]
    first = items[0]
    assert first["shipment_id"] == str(newer.shipment_id)
    assert first["risk_score"] == 0.9
    assert first["risk_level"] == "high"
    assert first["confidence"] == 0.9
    assert first["weather_summary"] == "ambient deviates 3.2°C from the safe band"
    assert first["predicted_at"]
    assert first["created_at"] == first["predicted_at"]


def test_history_paginates() -> None:
    now = datetime.now(UTC)
    items = [
        _make_prediction(risk_level="low", created_at=now - timedelta(hours=i))
        for i in range(5)
    ]
    app = _test_app(_history_service(items))
    page_one = TestClient(app).get("/api/v1/predictions/history?page=1&size=2")
    payload = page_one.json()["data"]
    assert payload["total"] == 5
    assert payload["pages"] == 3
    assert [item["id"] for item in payload["items"]] == [
        str(items[0].prediction_id),
        str(items[1].prediction_id),
    ]
    page_two = TestClient(app).get("/api/v1/predictions/history?page=2&size=2")
    assert [item["id"] for item in page_two.json()["data"]["items"]] == [
        str(items[2].prediction_id),
        str(items[3].prediction_id),
    ]


def test_history_filters_by_shipment_and_risk_level() -> None:
    target = uuid4()
    items = [
        _make_prediction(shipment_id=target, risk_level="high", risk_score=0.9),
        _make_prediction(shipment_id=target, risk_level="low", risk_score=0.1),
        _make_prediction(risk_level="high", risk_score=0.8),
    ]
    response = TestClient(_test_app(_history_service(items))).get(
        f"/api/v1/predictions/history?shipment_id={target}&risk_level=high"
    )
    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["total"] == 1
    assert len(payload["items"]) == 1
    item = payload["items"][0]
    assert item["shipment_id"] == str(target)
    assert item["risk_level"] == "high"
