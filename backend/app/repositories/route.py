"""SQLAlchemy async repositories for routes and waypoints."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

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
            .where(RouteModel.id == route_id)
        )
        model = result.scalar_one_or_none()
        return to_route_entity(model) if model else None

    async def list_for_shipment(self, shipment_id: UUID) -> list[Route]:
        result = await self._session.execute(
            select(RouteModel)
            .options(selectinload(RouteModel.waypoints))
            .where(RouteModel.shipment_id == shipment_id)
            .order_by(RouteModel.safety_score.desc())
        )
        return [to_route_entity(model) for model in result.scalars().all()]

    async def update(self, entity: Route) -> Route:
        result = await self._session.execute(
            select(RouteModel).where(RouteModel.id == entity.route_id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return entity
        model.distance_km = entity.distance_km
        model.duration_minutes = entity.duration_minutes
        model.stops = entity.stops
        model.polyline = entity.polyline
        model.weather_factor = entity.weather_factor
        model.safety_score = entity.safety_score
        model.is_selected = entity.is_selected
        await self._session.flush()
        return entity


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

    async def list_for_route(self, route_id: UUID) -> list[Waypoint]:
        result = await self._session.execute(
            select(WaypointModel)
            .where(WaypointModel.route_id == route_id)
            .order_by(WaypointModel.sequence)
        )
        return [to_waypoint_entity(model) for model in result.scalars().all()]

    async def update(self, entity: Waypoint) -> Waypoint:
        result = await self._session.execute(
            select(WaypointModel).where(WaypointModel.id == entity.waypoint_id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return entity
        model.sequence = entity.sequence
        model.name = entity.name
        model.latitude = entity.latitude
        model.longitude = entity.longitude
        model.arrival_at = entity.arrival_at
        model.departure_at = entity.departure_at
        await self._session.flush()
        return entity
