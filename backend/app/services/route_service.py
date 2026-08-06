"""Route management service.

Coordinates route CRUD, waypoint CRUD and the dedicated lifecycle workflows
(optimize, select/assign, complete, cancel). Business rules live on the
``Route``/``Waypoint`` entities (metric bounds, status transitions); the rule
that only one route per shipment may be selected is enforced here across the
injected repositories.
"""

import builtins
from uuid import UUID

from app.core.exceptions import NotFoundError, ValidationError
from app.domain.entities.route import Route, Waypoint
from app.domain.repositories import (
    RouteRepository,
    ShipmentRepository,
    WaypointRepository,
)
from app.schemas.route import (
    RouteCreate,
    RouteOptimizeUpdate,
    RouteUpdate,
    WaypointCreate,
    WaypointUpdate,
)


class RouteService:
    def __init__(
        self,
        route_repo: RouteRepository,
        waypoint_repo: WaypointRepository,
        shipment_repo: ShipmentRepository,
    ) -> None:
        self._routes = route_repo
        self._waypoints = waypoint_repo
        self._shipments = shipment_repo

    async def create(self, payload: RouteCreate) -> Route:
        shipment = await self._shipments.get(payload.shipment_id)
        if shipment is None:
            raise NotFoundError("Shipment not found")
        waypoints = [
            Waypoint.create(
                route_id=UUID(int=0),
                sequence=wp.sequence,
                name=wp.name,
                latitude=wp.latitude,
                longitude=wp.longitude,
                arrival_at=wp.arrival_at,
                departure_at=wp.departure_at,
            )
            for wp in payload.waypoints
        ]
        try:
            entity = Route.create(
                shipment_id=payload.shipment_id,
                distance_km=payload.distance_km,
                duration_minutes=payload.duration_minutes,
                stops=payload.stops,
                polyline=payload.polyline,
                weather_factor=payload.weather_factor,
                safety_score=payload.safety_score,
                is_selected=payload.is_selected,
                waypoints=waypoints,
                optimization_metadata=payload.optimization_metadata,
            )
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        for waypoint in entity.waypoints:
            waypoint.route_id = entity.route_id
        return await self._routes.create(entity)

    async def get(self, route_id: UUID) -> Route:
        entity = await self._routes.get(route_id)
        if entity is None:
            raise NotFoundError("Route not found")
        return entity

    async def list(
        self,
        *,
        shipment_id: UUID | None,
        status: str | None,
        is_selected: bool | None,
        page: int,
        size: int,
    ) -> tuple[list[Route], int]:
        offset = (page - 1) * size
        total = await self._routes.count(
            shipment_id=shipment_id, status=status, is_selected=is_selected
        )
        items = await self._routes.list_paginated(
            shipment_id=shipment_id,
            status=status,
            is_selected=is_selected,
            offset=offset,
            limit=size,
        )
        return items, total

    async def update(self, route_id: UUID, payload: RouteUpdate) -> Route:
        entity = await self.get(route_id)
        try:
            entity.update(
                distance_km=payload.distance_km,
                duration_minutes=payload.duration_minutes,
                stops=payload.stops,
                polyline=payload.polyline,
                weather_factor=payload.weather_factor,
                safety_score=payload.safety_score,
            )
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        return await self._routes.update(entity)

    async def optimize(self, route_id: UUID, payload: RouteOptimizeUpdate) -> Route:
        entity = await self.get(route_id)
        try:
            entity.update(
                distance_km=payload.distance_km,
                duration_minutes=payload.duration_minutes,
                stops=payload.stops,
                polyline=payload.polyline,
                weather_factor=payload.weather_factor,
                safety_score=payload.safety_score,
            )
            entity.mark_optimized(payload.optimization_metadata)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        return await self._routes.update(entity)

    async def select(self, route_id: UUID) -> Route:
        """Assign this route as the shipment's chosen route (one per shipment)."""
        entity = await self.get(route_id)
        try:
            entity.select()
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        for other in await self._routes.list_for_shipment(entity.shipment_id):
            if other.route_id != entity.route_id and other.is_selected:
                other.deselect()
                await self._routes.update(other)
        return await self._routes.update(entity)

    async def complete(self, route_id: UUID) -> Route:
        entity = await self.get(route_id)
        try:
            entity.complete()
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        return await self._routes.update(entity)

    async def cancel(self, route_id: UUID) -> Route:
        entity = await self.get(route_id)
        try:
            entity.cancel()
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        return await self._routes.update(entity)

    async def delete(self, route_id: UUID) -> Route:
        entity = await self.get(route_id)
        entity.soft_delete()
        await self._routes.soft_delete(route_id)
        return entity

    async def list_waypoints(self, route_id: UUID) -> builtins.list[Waypoint]:
        await self.get(route_id)
        return await self._waypoints.list_for_route(route_id)

    async def add_waypoint(self, route_id: UUID, payload: WaypointCreate) -> Waypoint:
        entity = await self.get(route_id)
        try:
            waypoint = Waypoint.create(
                route_id=route_id,
                sequence=payload.sequence,
                name=payload.name,
                latitude=payload.latitude,
                longitude=payload.longitude,
                arrival_at=payload.arrival_at,
                departure_at=payload.departure_at,
            )
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        entity.add_waypoint(waypoint)
        await self._routes.update(entity)
        return await self._waypoints.create(waypoint)

    async def update_waypoint(self, waypoint_id: UUID, payload: WaypointUpdate) -> Waypoint:
        waypoint = await self._waypoints.get(waypoint_id)
        if waypoint is None:
            raise NotFoundError("Waypoint not found")
        try:
            waypoint.update(
                sequence=payload.sequence,
                name=payload.name,
                latitude=payload.latitude,
                longitude=payload.longitude,
                arrival_at=payload.arrival_at,
                departure_at=payload.departure_at,
            )
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        return await self._waypoints.update(waypoint)

    async def delete_waypoint(self, waypoint_id: UUID) -> Waypoint:
        waypoint = await self._waypoints.get(waypoint_id)
        if waypoint is None:
            raise NotFoundError("Waypoint not found")
        await self._waypoints.delete(waypoint_id)
        return waypoint
