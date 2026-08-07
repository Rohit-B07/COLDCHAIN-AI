"""Analytics endpoints: aggregated operational insights."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps.container import get_analytics_service
from app.api.deps.rbac import require_permissions
from app.domain.permissions import Permission
from app.schemas.analytics import AnalyticsDashboardResponse
from app.schemas.common import ApiResponse
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])

_ViewAnalytics = Depends(require_permissions(Permission.ALERT_VIEW))


@router.get(
    "/dashboard",
    response_model=ApiResponse[AnalyticsDashboardResponse],
    summary="Aggregated operational KPIs for the analytics dashboard",
    dependencies=[_ViewAnalytics],
)
async def get_analytics_dashboard(
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
) -> ApiResponse[AnalyticsDashboardResponse]:
    return ApiResponse(data=await service.get_dashboard())
