"""API tests for advanced shipment search and filtering (no live DB).

The RBAC middleware and route-level permission dependency are bypassed by
overriding the role and service dependencies, so the route logic (filter
mapping, pagination, sorting, presentation) is exercised against an in-memory
fake repository. A separate test hits the real application to assert that the
endpoint is protected and rejects unauthenticated callers.
"""

from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode
from uuid import UUID, uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.deps.container import get_shipment_service
from app.api.deps.rbac import get_user_roles
from app.api.errors import register_exception_handlers
from app.api.routes import api_router
from app.core.config import get_settings
from app.core.rbac import Role
from app.domain.entities.shipment import Shipment
from app.domain.value_objects import Priority, ShipmentStatus
from app.main import app as real_app
from app.services.shipment_service import ShipmentService


def _make_shipment(
    *,
    shipment_id: UUID | None = None,
    tracking_code: str | None = None,
    vaccine_name: str = "Pfizer-BioNTech",
    priority: Priority = Priority.MEDIUM,
    status: ShipmentStatus = ShipmentStatus.CREATED,
    warehouse_id: UUID | None = None,
    destination_id: UUID | None = None,
    created_at: datetime | None = None,
    estimated_delivery_at: datetime | None = None,
) -> Shipment:
    return Shipment(
        shipment_id=shipment_id or uuid4(),
        tracking_code=tracking_code or f"SHP-{uuid4().hex[:10].upper()}",
        vaccine_name=vaccine_name,
        dose_count=100,
        priority=priority,
        temperature_min=2.0,
        temperature_max=8.0,
        warehouse_id=warehouse_id or uuid4(),
        destination_id=destination_id or uuid4(),
        container_id=None,
        driver_id=None,
        status=status,
        created_at=created_at or datetime.now(UTC),
        estimated_delivery_at=estimated_delivery_at,
    )


class _FakeShipmentRepo:
    def __init__(self, shipments: list[Shipment]) -> None:
        self._items = list(shipments)

    async def count(
        self,
        *,
        search: str | None = None,
        shipment_id: UUID | None = None,
        tracking_code: str | None = None,
        origin: UUID | None = None,
        destination: UUID | None = None,
        status: str | None = None,
        priority: str | None = None,
        vaccine_type: str | None = None,
        created_after: datetime | None = None,
        created_before: datetime | None = None,
        expected_delivery_after: datetime | None = None,
        expected_delivery_before: datetime | None = None,
    ) -> int:
        return len(
            self._apply(
                search=search,
                shipment_id=shipment_id,
                tracking_code=tracking_code,
                origin=origin,
                destination=destination,
                status=status,
                priority=priority,
                vaccine_type=vaccine_type,
                created_after=created_after,
                created_before=created_before,
                expected_delivery_after=expected_delivery_after,
                expected_delivery_before=expected_delivery_before,
            )
        )

    async def list_paginated(
        self,
        *,
        search: str | None = None,
        shipment_id: UUID | None = None,
        tracking_code: str | None = None,
        origin: UUID | None = None,
        destination: UUID | None = None,
        status: str | None = None,
        priority: str | None = None,
        vaccine_type: str | None = None,
        created_after: datetime | None = None,
        created_before: datetime | None = None,
        expected_delivery_after: datetime | None = None,
        expected_delivery_before: datetime | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        offset: int = 0,
        limit: int = 20,
    ) -> list[Shipment]:
        items = self._apply(
            search=search,
            shipment_id=shipment_id,
            tracking_code=tracking_code,
            origin=origin,
            destination=destination,
            status=status,
            priority=priority,
            vaccine_type=vaccine_type,
            created_after=created_after,
            created_before=created_before,
            expected_delivery_after=expected_delivery_after,
            expected_delivery_before=expected_delivery_before,
        )
        items.sort(
            key=self._sort_key(sort_by),
            reverse=(sort_order != "asc"),
        )
        return items[offset : offset + limit]

    def _sort_key(self, sort_by: str):
        keys = {
            "created_at": lambda s: s.created_at or datetime.min(UTC),
            "tracking_code": lambda s: s.tracking_code,
            "status": lambda s: s.status.value,
            "priority": lambda s: s.priority.value,
            "vaccine_name": lambda s: s.vaccine_name,
            "estimated_delivery_at": lambda s: s.estimated_delivery_at
            or datetime.min(UTC),
        }
        return keys.get(sort_by, keys["created_at"])

    def _apply(
        self,
        *,
        search: str | None,
        shipment_id: UUID | None,
        tracking_code: str | None,
        origin: UUID | None,
        destination: UUID | None,
        status: str | None,
        priority: str | None,
        vaccine_type: str | None,
        created_after: datetime | None,
        created_before: datetime | None,
        expected_delivery_after: datetime | None,
        expected_delivery_before: datetime | None,
    ) -> list[Shipment]:
        items = list(self._items)
        if search:
            pattern = search.strip().lower()
            items = [
                s
                for s in items
                if pattern in s.tracking_code.lower()
                or pattern in s.vaccine_name.lower()
            ]
        if shipment_id is not None:
            items = [s for s in items if s.shipment_id == shipment_id]
        if tracking_code:
            pattern = tracking_code.strip().upper()
            items = [s for s in items if pattern in s.tracking_code.upper()]
        if origin is not None:
            items = [s for s in items if s.warehouse_id == origin]
        if destination is not None:
            items = [s for s in items if s.destination_id == destination]
        if status:
            items = [s for s in items if s.status.value == status.strip().lower()]
        if priority:
            items = [s for s in items if s.priority.value == priority.strip().lower()]
        if vaccine_type:
            pattern = vaccine_type.strip().lower()
            items = [s for s in items if pattern in s.vaccine_name.lower()]
        if created_after is not None:
            items = [
                s for s in items if (s.created_at or datetime.min(UTC)) >= created_after
            ]
        if created_before is not None:
            items = [
                s
                for s in items
                if (s.created_at or datetime.min(UTC)) <= created_before
            ]
        if expected_delivery_after is not None:
            items = [
                s
                for s in items
                if (s.estimated_delivery_at or datetime.min(UTC))
                >= expected_delivery_after
            ]
        if expected_delivery_before is not None:
            items = [
                s
                for s in items
                if (s.estimated_delivery_at or datetime.min(UTC))
                <= expected_delivery_before
            ]
        return items


def _service(shipments: list[Shipment]) -> ShipmentService:
    return ShipmentService(
        shipment_repo=_FakeShipmentRepo(shipments),
        warehouse_repo=object(),  # type: ignore[arg-type]
        phc_repo=object(),  # type: ignore[arg-type]
        container_repo=object(),  # type: ignore[arg-type]
        driver_repo=object(),  # type: ignore[arg-type]
    )


def _test_app(service: ShipmentService) -> FastAPI:
    settings = get_settings()
    application = FastAPI()
    application.include_router(api_router, prefix=settings.API_V1_STR)
    register_exception_handlers(application)
    application.dependency_overrides[get_user_roles] = lambda: frozenset({Role.ADMIN})
    application.dependency_overrides[get_shipment_service] = lambda: service
    return application


def test_list_shipments_requires_authentication() -> None:
    response = TestClient(real_app).get("/api/v1/shipments")
    assert response.status_code == 401


def test_list_shipments_returns_empty_page() -> None:
    response = TestClient(_test_app(_service([]))).get("/api/v1/shipments")
    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["items"] == []
    assert payload["total"] == 0
    assert payload["page"] == 1
    assert payload["size"] == 20
    assert payload["pages"] == 0


def test_keyword_search_matches_tracking_code_and_vaccine() -> None:
    target = _make_shipment(
        tracking_code="SHP-ABCDEF1234", vaccine_name="Pfizer-BioNTech"
    )
    other = _make_shipment(tracking_code="SHP-ZZZZZZ9999", vaccine_name="Covaxin")
    app = _test_app(_service([target, other]))

    by_code = TestClient(app).get("/api/v1/shipments?search=ABCDEF")
    assert by_code.json()["data"]["total"] == 1
    assert by_code.json()["data"]["items"][0]["id"] == str(target.shipment_id)

    by_vaccine = TestClient(app).get("/api/v1/shipments?search=covaxin")
    assert by_vaccine.json()["data"]["total"] == 1
    assert by_vaccine.json()["data"]["items"][0]["id"] == str(other.shipment_id)


def test_list_shipments_paginates() -> None:
    now = datetime.now(UTC)
    items = [_make_shipment(created_at=now - timedelta(hours=i)) for i in range(5)]
    app = _test_app(_service(items))
    page_one = TestClient(app).get("/api/v1/shipments?page=1&size=2")
    payload = page_one.json()["data"]
    assert payload["total"] == 5
    assert payload["pages"] == 3
    assert [item["id"] for item in payload["items"]] == [
        str(items[0].shipment_id),
        str(items[1].shipment_id),
    ]
    page_two = TestClient(app).get("/api/v1/shipments?page=2&size=2")
    assert [item["id"] for item in page_two.json()["data"]["items"]] == [
        str(items[2].shipment_id),
        str(items[3].shipment_id),
    ]


def test_sorting_ascending_and_descending() -> None:
    alpha = _make_shipment(tracking_code="SHP-AAAAAA0001", vaccine_name="Covaxin")
    bravo = _make_shipment(tracking_code="SHP-BBBBBB0002", vaccine_name="Pfizer")
    app = _test_app(_service([bravo, alpha]))

    asc = TestClient(app).get("/api/v1/shipments?sort_by=tracking_code&sort_order=asc")
    assert [item["id"] for item in asc.json()["data"]["items"]] == [
        str(alpha.shipment_id),
        str(bravo.shipment_id),
    ]

    desc = TestClient(app).get(
        "/api/v1/shipments?sort_by=tracking_code&sort_order=desc"
    )
    assert [item["id"] for item in desc.json()["data"]["items"]] == [
        str(bravo.shipment_id),
        str(alpha.shipment_id),
    ]


def test_combined_filters() -> None:
    warehouse = uuid4()
    destination = uuid4()
    target = _make_shipment(
        tracking_code="SHP-HIGH123456",
        vaccine_name="AstraZeneca",
        priority=Priority.HIGH,
        status=ShipmentStatus.IN_TRANSIT,
        warehouse_id=warehouse,
        destination_id=destination,
        created_at=datetime.now(UTC) - timedelta(days=1),
        estimated_delivery_at=datetime.now(UTC) + timedelta(days=3),
    )
    wrong_status = _make_shipment(
        tracking_code="SHP-HIGH654321",
        vaccine_name="AstraZeneca",
        priority=Priority.HIGH,
        status=ShipmentStatus.CREATED,
        warehouse_id=warehouse,
        destination_id=destination,
        created_at=datetime.now(UTC) - timedelta(days=1),
    )
    wrong_vaccine = _make_shipment(
        tracking_code="SHP-HIGH111111",
        vaccine_name="Covaxin",
        priority=Priority.HIGH,
        status=ShipmentStatus.IN_TRANSIT,
        warehouse_id=warehouse,
        destination_id=destination,
        created_at=datetime.now(UTC) - timedelta(days=1),
    )
    app = _test_app(_service([target, wrong_status, wrong_vaccine]))

    created_after = datetime.now(UTC) - timedelta(days=2)
    query = urlencode(
        {
            "status": "in_transit",
            "priority": "high",
            "vaccine_type": "astra",
            "origin": str(warehouse),
            "destination": str(destination),
            "created_after": created_after.isoformat(),
            "expected_delivery_after": created_after.isoformat(),
        }
    )
    response = TestClient(app).get(f"/api/v1/shipments?{query}")
    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["total"] == 1
    assert payload["items"][0]["id"] == str(target.shipment_id)


def test_filter_with_no_matches_returns_empty_page() -> None:
    item = _make_shipment(status=ShipmentStatus.DELIVERED)
    app = _test_app(_service([item]))
    response = TestClient(app).get("/api/v1/shipments?status=in_transit")
    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["total"] == 0
    assert payload["items"] == []


def test_invalid_sort_field_is_rejected() -> None:
    response = TestClient(_test_app(_service([]))).get(
        "/api/v1/shipments?sort_by=not_a_column"
    )
    assert response.status_code == 422


def test_invalid_shipment_id_is_rejected() -> None:
    response = TestClient(_test_app(_service([]))).get(
        "/api/v1/shipments?shipment_id=not-a-uuid"
    )
    assert response.status_code == 422


def test_invalid_created_range_is_rejected() -> None:
    query = urlencode(
        {
            "created_after": datetime.now(UTC).isoformat(),
            "created_before": (datetime.now(UTC) - timedelta(days=1)).isoformat(),
        }
    )
    response = TestClient(_test_app(_service([]))).get(f"/api/v1/shipments?{query}")
    assert response.status_code == 422
