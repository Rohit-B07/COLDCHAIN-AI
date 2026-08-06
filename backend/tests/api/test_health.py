"""API layer tests using FastAPI's TestClient.

The health endpoint is tested with an in-memory fake repository wired via
dependency override, so these tests require no live database.
"""

from fastapi.testclient import TestClient

from app.api.deps.container import get_check_health
from app.main import app
from app.use_cases.health import CheckHealth


class _FakeRepo:
    def ping(self) -> bool:
        return True


client = TestClient(app)


def test_health_returns_ok(monkeypatch) -> None:
    def _fake_check() -> CheckHealth:
        return CheckHealth(health_repo=_FakeRepo())  # type: ignore[arg-type]

    app.dependency_overrides[get_check_health] = _fake_check
    try:
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        payload = response.json()
        assert payload["success"] is True
        assert payload["data"]["status"] == "ok"
        assert payload["data"]["database"] == "ok"
    finally:
        app.dependency_overrides.clear()


def test_root_returns_app_name() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["name"] == "ColdChain AI API"
