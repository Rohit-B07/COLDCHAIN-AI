"""Unit tests for application-layer use cases (no DB or network)."""

from app.domain.repositories import HealthRepository
from app.use_cases.health import CheckHealth


class FakeHealthRepository(HealthRepository):
    """In-memory stand-in for the health repository port."""

    def __init__(self, reachable: bool = True) -> None:
        self._reachable = reachable

    async def ping(self) -> bool:
        return self._reachable


class TestCheckHealth:
    async def test_reports_ok_when_database_reachable(self) -> None:
        use_case = CheckHealth(health_repo=FakeHealthRepository(reachable=True))
        result = await use_case.execute()
        assert result.status == "ok"
        assert result.database == "ok"

    async def test_reports_db_unavailable_when_not_reachable(self) -> None:
        use_case = CheckHealth(health_repo=FakeHealthRepository(reachable=False))
        result = await use_case.execute()
        assert result.status == "ok"
        assert result.database == "unavailable"
