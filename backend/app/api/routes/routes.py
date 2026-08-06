"""Route endpoints: route CRUD, lifecycle workflows and waypoint CRUD."""

from typing import Annotated, cast
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.deps.container import get_route_service
from app.api.deps.rbac import require_permissions
from app.domain.entities.route import Route, Waypoint
from app.domain.permissions import Permission
from app.schemas.common import ApiResponse, Page
from app.schemas.route import (
    RouteCreate,
    RouteOptimizeUpdate,
    RouteQueryParams,
    RouteRead,
    RouteStatusUpdate,
    RouteStatusValue,
    RouteUpdate,
    WaypointCreate,
    WaypointRead,
    WaypointUpdate,
)
from app.services.route_service import RouteService

router = APIRouter(prefix="/routes", tags=["routes"])

_ViewRoutes = Depends(require_permissions(Permission.ROUTE_VIEW))
_PlanRoutes = Depends(require_permissions(Permission.ROUTE_PLAN))
_ManageRoutes = Depends(require_permissions(Permission.ROUTE_UPDATE))
_SelectRoutes = Depends(require_permissions(Permission.ROUTE_SELECT))


def _read_waypoint(w: Waypoint) -> WaypointRead:
    return WaypointRead(
        id=w.waypoint_id,
        route_id=w.route_id,
        sequence=w.sequence,
        name=w.name,
        latitude=w.latitude,
        longitude=w.longitude,
        arrival_at=w.arrival_at,
        departure_at=w.departure_at,
    )


def _read(route: Route) -> RouteRead:
    return RouteRead(
        id=route.route_id,
        shipment_id=route.shipment_id,
        distance_km=route.distance_km,
        duration_minutes=route.duration_minutes,
        stops=route.stops,
        polyline=route.polyline,
        weather_factor=route.weather_factor,
        safety_score=route.safety_score,
        is_selected=route.is_selected,
        status=cast(RouteStatusValue, route.status),
        optimization_metadata=route.optimization_metadata,
        waypoints=[_read_waypoint(w) for w in route.waypoints],
        is_deleted=route.is_deleted,
        created_at=route.created_at,
    )


@router.get(
    "",
    response_model=ApiResponse[Page[RouteRead]],
    summary="List routes (paginated and filtered)",
    dependencies=[_ViewRoutes],
)
async def list_routes(
    params: Annotated[RouteQueryParams, Query()],
    service: Annotated[RouteService, Depends(get_route_service)],
) -> ApiResponse[Page[RouteRead]]:
    items, total = await service.list(
        shipment_id=params.shipment_id,
        status=params.status,
        is_selected=params.is_selected,
        page=params.page,
        size=params.size,
    )
    pages = (total + params.size - 1) // params.size if total else 0
    return ApiResponse(
        data=Page[RouteRead](
            items=[_read(route) for route in items],
            total=total,
            page=params.page,
            size=params.size,
            pages=pages,
        )
    )


@router.post(
    "",
    response_model=ApiResponse[RouteRead],
    status_code=201,
    summary="Create a route for a shipment",
    dependencies=[_PlanRoutes],
)
async def create_route(
    payload: RouteCreate,
    service: Annotated[RouteService, Depends(get_route_service)],
) -> ApiResponse[RouteRead]:
    entity = await service.create(payload)
    return ApiResponse(data=_read(entity))


@router.get(
    "/{route_id}",
    response_model=ApiResponse[RouteRead],
    summary="Get a route by id",
    dependencies=[_ViewRoutes],
)
async def get_route(
    route_id: UUID,
    service: Annotated[RouteService, Depends(get_route_service)],
) -> ApiResponse[RouteRead]:
    entity = await service.get(route_id)
    return ApiResponse(data=_read(entity))


@router.patch(
    "/{route_id}",
    response_model=ApiResponse[RouteRead],
    summary="Update a route's metrics",
    dependencies=[_ManageRoutes],
)
async def update_route(
    route_id: UUID,
    payload: RouteUpdate,
    service: Annotated[RouteService, Depends(get_route_service)],
) -> ApiResponse[RouteRead]:
    entity = await service.update(route_id, payload)
    return ApiResponse(data=_read(entity))


@router.patch(
    "/{route_id}/optimize",
    response_model=ApiResponse[RouteRead],
    summary="Record optimized route metrics and mark as optimized",
    dependencies=[_ManageRoutes],
)
async def optimize_route(
    route_id: UUID,
    payload: RouteOptimizeUpdate,
    service: Annotated[RouteService, Depends(get_route_service)],
) -> ApiResponse[RouteRead]:
    entity = await service.optimize(route_id, payload)
    return ApiResponse(data=_read(entity))


@router.post(
    "/{route_id}/select",
    response_model=ApiResponse[RouteRead],
    summary="Assign this route as the shipment's selected route",
    dependencies=[_SelectRoutes],
)
async def select_route(
    route_id: UUID,
    service: Annotated[RouteService, Depends(get_route_service)],
) -> ApiResponse[RouteRead]:
    entity = await service.select(route_id)
    return ApiResponse(data=_read(entity))


@router.patch(
    "/{route_id}/status",
    response_model=ApiResponse[RouteRead],
    summary="Transition a route's lifecycle status",
    dependencies=[_ManageRoutes],
)
async def update_route_status(
    route_id: UUID,
    payload: RouteStatusUpdate,
    service: Annotated[RouteService, Depends(get_route_service)],
) -> ApiResponse[RouteRead]:
    if payload.status == "optimized":
        entity = await service.optimize(route_id, RouteOptimizeUpdate())
    elif payload.status == "selected":
        entity = await service.select(route_id)
    elif payload.status == "completed":
        entity = await service.complete(route_id)
    elif payload.status == "cancelled":
        entity = await service.cancel(route_id)
    else:
        entity = await service.get(route_id)
    return ApiResponse(data=_read(entity))


@router.delete(
    "/{route_id}",
    response_model=ApiResponse[RouteRead],
    summary="Soft-delete a route",
    dependencies=[_ManageRoutes],
)
async def delete_route(
    route_id: UUID,
    service: Annotated[RouteService, Depends(get_route_service)],
) -> ApiResponse[RouteRead]:
    entity = await service.delete(route_id)
    return ApiResponse(data=_read(entity))


@router.get(
    "/{route_id}/waypoints",
    response_model=ApiResponse[list[WaypointRead]],
    summary="List a route's waypoints in sequence order",
    dependencies=[_ViewRoutes],
)
async def list_waypoints(
    route_id: UUID,
    service: Annotated[RouteService, Depends(get_route_service)],
) -> ApiResponse[list[WaypointRead]]:
    waypoints = await service.list_waypoints(route_id)
    return ApiResponse(data=[_read_waypoint(w) for w in waypoints])


@router.post(
    "/{route_id}/waypoints",
    response_model=ApiResponse[WaypointRead],
    status_code=201,
    summary="Add a waypoint to a route",
    dependencies=[_ManageRoutes],
)
async def add_waypoint(
    route_id: UUID,
    payload: WaypointCreate,
    service: Annotated[RouteService, Depends(get_route_service)],
) -> ApiResponse[WaypointRead]:
    waypoint = await service.add_waypoint(route_id, payload)
    return ApiResponse(data=_read_waypoint(waypoint))


@router.patch(
    "/{route_id}/waypoints/{waypoint_id}",
    response_model=ApiResponse[WaypointRead],
    summary="Update a waypoint",
    dependencies=[_ManageRoutes],
)
async def update_waypoint(
    route_id: UUID,
    waypoint_id: UUID,
    payload: WaypointUpdate,
    service: Annotated[RouteService, Depends(get_route_service)],
) -> ApiResponse[WaypointRead]:
    waypoint = await service.update_waypoint(waypoint_id, payload)
    return ApiResponse(data=_read_waypoint(waypoint))


@router.delete(
    "/{route_id}/waypoints/{waypoint_id}",
    response_model=ApiResponse[WaypointRead],
    summary="Delete a waypoint",
    dependencies=[_ManageRoutes],
)
async def delete_waypoint(
    route_id: UUID,
    waypoint_id: UUID,
    service: Annotated[RouteService, Depends(get_route_service)],
) -> ApiResponse[WaypointRead]:
    waypoint = await service.delete_waypoint(waypoint_id)
    return ApiResponse(data=_read_waypoint(waypoint))
