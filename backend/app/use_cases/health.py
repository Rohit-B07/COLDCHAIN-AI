"""Health check use case.

Reports service liveness and optional database connectivity. This is the first
concrete use case and demonstrates the Clean Architecture wiring: the use case
depends on the `HealthRepository` port, which is injected from the API layer.
"""

from dataclasses import dataclass

from app.domain.repositories import HealthRepository


@dataclass
class HealthResult:
    """Outcome of a health check."""

    status: str
    database: str


class CheckHealth:
    """Application service that checks service + database health."""

    def __init__(self, health_repo: HealthRepository) -> None:
        self._health_repo = health_repo

    async def execute(self) -> HealthResult:
        db_ok = await self._health_repo.ping()
        return HealthResult(
            status="ok",
            database="ok" if db_ok else "unavailable",
        )
