"""SQLAlchemy async repositories for routes and waypoints."""

import builtins
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundError
from app.domain.entities.route import Route, Waypoint
from app.models.route import Route as RouteModel, Waypoint as WaypointModel
from app.repositories.base import to_route_entity, to_waypoint_entity


class SqlAlchemyRouteRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, entity: Route) -> Route:
        model = RouteModel(
            id=entity.route_id,
            shipment_id=entity.shipment_id,
            distance_km=entity.distance_km,
            duration_minutes=entity.duration_minutes,
            stops=entity.stops,
            polyline=entity.polyline,
            weather_factor=entity.weather_factor,
            safety_score=entity.safety_score,
            is_selected=entity.is_selected,
            status_state=entity.status,
            optimization_metadata=entity.optimization_metadata,
        )
        self._session.add(model)
        for waypoint in entity.waypoints:
            self._session.add(
                WaypointModel(
                    id=waypoint.waypoint_id,
                    route_id=entity.route_id,
                    sequence=waypoint.sequence,
                    name=waypoint.name,
                    latitude=waypoint.latitude,
                    longitude=waypoint.longitude,
                    arrival_at=waypoint.arrival_at,
                    departure_at=waypoint.departure_at,
                )
            )
        await self._session.flush()
        return entity

    async def get(self, route_id: UUID) -> Route | None:
        result = await self._session.execute(
            select(RouteModel)
            .options(selectinload(RouteModel.waypoints))
            .where(
                RouteModel.id == route_id,
                RouteModel.is_deleted.is_(False),
            )
        )
        model = result.scalar_one_or_none()
        return to_route_entity(model) if model else None

    async def list_for_shipment(self, shipment_id: UUID) -> builtins.list[Route]:
        result = await self._session.execute(
            select(RouteModel)
            .options(selectinload(RouteModel.waypoints))
            .where(
                RouteModel.shipment_id == shipment_id,
                RouteModel.is_deleted.is_(False),
            )
            .order_by(RouteModel.safety_score.desc())
        )
        return [to_route_entity(model) for model in result.scalars().all()]

    async def update(self, entity: Route) -> Route:
        model = await self._session.get(RouteModel, entity.route_id)
        if model is None:
            raise NotFoundError("Route not found")
        model.distance_km = entity.distance_km
        model.duration_minutes = entity.duration_minutes
        model.stops = entity.stops
        model.polyline = entity.polyline
        model.weather_factor = entity.weather_factor
        model.safety_score = entity.safety_score
        model.is_selected = entity.is_selected
        model.status_state = entity.status
        model.optimization_metadata = entity.optimization_metadata
        await self._session.flush()
        return entity

    async def count(
        self,
        *,
        shipment_id: UUID | None = None,
        status: str | None = None,
        is_selected: bool | None = None,
    ) -> int:
        query = self._apply_filters(
            select(func.count(RouteModel.id)),
            shipment_id=shipment_id,
            status=status,
            is_selected=is_selected,
        ).where(RouteModel.is_deleted.is_(False))
        result = await self._session.execute(query)
        return int(result.scalar_one())

    async def list_paginated(
        self,
        *,
        shipment_id: UUID | None = None,
        status: str | None = None,
        is_selected: bool | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> builtins.list[Route]:
        query = self._apply_filters(
            select(RouteModel),
            shipment_id=shipment_id,
            status=status,
            is_selected=is_selected,
        ).where(RouteModel.is_deleted.is_(False))
        query = query.order_by(RouteModel.safety_score.desc()).offset(offset).limit(limit)
        result = await self._session.execute(query)
        return [to_route_entity(model) for model in result.scalars().all()]

    async def soft_delete(self, route_id: UUID) -> Route | None:
        model = await self._session.get(RouteModel, route_id)
        if model is None:
            return None
        model.is_deleted = True
        model.deleted_at = datetime.now(UTC)
        await self._session.flush()
        return to_route_entity(model)

    def _apply_filters(
        self,
        query: Select,
        *,
        shipment_id: UUID | None,
        status: str | None,
        is_selected: bool | None,
    ) -> Select:
        if shipment_id is not None:
            query = query.where(RouteModel.shipment_id == shipment_id)
        if status:
            query = query.where(RouteModel.status_state == status.strip().lower())
        if is_selected is not None:
            query = query.where(RouteModel.is_selected.is_(is_selected))
        return query


class SqlAlchemyWaypointRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, entity: Waypoint) -> Waypoint:
        self._session.add(
            WaypointModel(
                id=entity.waypoint_id,
                route_id=entity.route_id,
                sequence=entity.sequence,
                name=entity.name,
                latitude=entity.latitude,
                longitude=entity.longitude,
                arrival_at=entity.arrival_at,
                departure_at=entity.departure_at,
            )
        )
        await self._session.flush()
        return entity

    async def get(self, waypoint_id: UUID) -> Waypoint | None:
        result = await self._session.execute(
            select(WaypointModel).where(WaypointModel.id == waypoint_id)
        )
        model = result.scalar_one_or_none()
        return to_waypoint_entity(model) if model else None

    async def list_for_route(self, route_id: UUID) -> builtins.list[Waypoint]:
        result = await self._session.execute(
            select(WaypointModel)
            .where(WaypointModel.route_id == route_id)
            .order_by(WaypointModel.sequence)
        )
        return [to_waypoint_entity(model) for model in result.scalars().all()]

    async def update(self, entity: Waypoint) -> Waypoint:
        model = await self._session.get(WaypointModel, entity.waypoint_id)
        if model is None:
            raise NotFoundError("Waypoint not found")
        model.sequence = entity.sequence
        model.name = entity.name
        model.latitude = entity.latitude
        model.longitude = entity.longitude
        model.arrival_at = entity.arrival_at
        model.departure_at = entity.departure_at
        await self._session.flush()
        return entity

    async def delete(self, waypoint_id: UUID) -> Waypoint | None:
        model = await self._session.get(WaypointModel, waypoint_id)
        if model is None:
            return None
        await self._session.delete(model)
        await self._session.flush()
        return None
