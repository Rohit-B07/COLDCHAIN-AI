"""Health check endpoint.

Exposes liveness and database readiness. The handler delegates to the
`CheckHealth` use case and never talks to the database directly. Dependency
injection is handled by FastAPI's `Depends`.
"""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps.container import get_check_health
from app.schemas.common import ApiResponse
from app.use_cases.health import CheckHealth, HealthResult

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=ApiResponse, summary="Service health check")
async def health(
    check: Annotated[CheckHealth, Depends(get_check_health)],
) -> ApiResponse:
    """Return service and database health status."""
    result: HealthResult = await check.execute()
    return ApiResponse(data={"status": result.status, "database": result.database})
