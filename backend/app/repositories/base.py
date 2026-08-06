"""Shared ORM -> domain entity mapping helpers."""

from app.domain.entities.facility import PrimaryHealthCentre, Warehouse
from app.domain.entities.intelligence import ColdAlert, Prediction, WeatherSnapshot
from app.domain.entities.logistics import ColdContainer, Driver, Vehicle
from app.domain.entities.role import Role
from app.domain.entities.route import Route, Waypoint
from app.domain.entities.shipment import Shipment
from app.domain.entities.user import User
from app.domain.value_objects import Priority, RiskLevel, ShipmentStatus, UserRole
from app.models.route import Route as RouteModel, Waypoint as WaypointModel


def to_role_entity(model) -> Role:
    return Role(
        role_id=model.id,
        name=model.name,
        description=model.description,
        is_deleted=model.is_deleted,
    )


def to_user_entity(model) -> User:
    return User(
        user_id=model.id,
        email=model.email,
        full_name=model.full_name,
        password_hash=model.password_hash,
        role=UserRole(model.role) if model.role else UserRole.LOGISTICS,
        is_active=model.is_active,
        created_at=model.created_at,
    )


def to_warehouse_entity(model) -> Warehouse:
    return Warehouse(
        warehouse_id=model.id,
        name=model.name,
        code=model.code,
        latitude=model.latitude,
        longitude=model.longitude,
        address=model.address,
        capacity=model.capacity,
        is_deleted=model.is_deleted,
        created_at=model.created_at,
    )


def to_phc_entity(model) -> PrimaryHealthCentre:
    return PrimaryHealthCentre(
        phc_id=model.id,
        name=model.name,
        code=model.code,
        district=model.district,
        state=model.state,
        latitude=model.latitude,
        longitude=model.longitude,
        contact=model.contact,
        capacity=model.capacity,
        priority_level=model.priority_level,
        is_deleted=model.is_deleted,
        created_at=model.created_at,
    )


def to_driver_entity(model) -> Driver:
    return Driver(
        driver_id=model.id,
        name=model.name,
        phone=model.phone,
        license_number=model.license_number,
        status=model.status,
        vehicle_id=model.vehicle_id,
        is_deleted=model.is_deleted,
        created_at=model.created_at,
    )


def to_vehicle_entity(model) -> Vehicle:
    return Vehicle(
        vehicle_id=model.id,
        registration_number=model.registration_number,
        vehicle_type=model.vehicle_type,
        capacity_kg=model.capacity_kg,
        is_reefer=model.is_reefer,
        status=model.status,
        maintenance_status=model.maintenance_status,
        last_maintenance_at=model.last_maintenance_at,
        next_maintenance_due_at=model.next_maintenance_due_at,
        is_deleted=model.is_deleted,
        created_at=model.created_at,
    )


def to_container_entity(model) -> ColdContainer:
    return ColdContainer(
        container_id=model.id,
        asset_tag=model.asset_tag,
        temperature_setpoint=model.temperature_setpoint,
        min_temperature=model.min_temperature,
        max_temperature=model.max_temperature,
        status=model.status,
        current_latitude=model.current_latitude,
        current_longitude=model.current_longitude,
        battery_level=model.battery_level,
    )


def to_shipment_entity(model) -> Shipment:
    return Shipment(
        shipment_id=model.id,
        tracking_code=model.tracking_code,
        vaccine_name=model.vaccine_name,
        dose_count=model.dose_count,
        priority=Priority(model.priority),
        temperature_min=model.temperature_min,
        temperature_max=model.temperature_max,
        warehouse_id=model.warehouse_id,
        destination_id=model.destination_id,
        container_id=model.container_id,
        driver_id=model.driver_id,
        status=ShipmentStatus(model.status_state),
        dispatched_at=model.dispatched_at,
        delivered_at=model.delivered_at,
        estimated_delivery_at=model.estimated_delivery_at,
        created_at=model.created_at,
        is_deleted=model.is_deleted,
        deleted_at=model.deleted_at,
    )


def to_prediction_entity(model) -> Prediction:
    return Prediction(
        prediction_id=model.id,
        shipment_id=model.shipment_id,
        excursion_risk=model.excursion_risk,
        risk_level=RiskLevel(model.risk_level).value,
        confidence=model.confidence,
        expected_min_temp=model.expected_min_temp,
        expected_max_temp=model.expected_max_temp,
        model_version=model.model_version,
        features=model.features,
        explanations=model.explanations,
        created_at=model.created_at,
    )


def to_weather_entity(model) -> WeatherSnapshot:
    return WeatherSnapshot(
        latitude=model.latitude,
        longitude=model.longitude,
        temperature_c=model.temperature_c,
        condition=model.condition,
        humidity_pct=model.humidity_pct,
        wind_kmh=model.wind_kmh,
        precipitation_mm=model.precipitation_mm,
        is_mock=model.is_mock,
    )


def to_alert_entity(model) -> ColdAlert:
    return ColdAlert(
        alert_id=model.id,
        severity=model.severity,
        alert_type=model.alert_type,
        message=model.message,
        shipment_id=model.shipment_id,
        container_id=model.container_id,
        status=model.status,
        acknowledged_by=model.acknowledged_by,
        acknowledged_at=model.acknowledged_at,
        created_at=model.created_at,
    )


def to_waypoint_entity(model: WaypointModel) -> Waypoint:
    return Waypoint(
        waypoint_id=model.id,
        route_id=model.route_id,
        sequence=model.sequence,
        name=model.name,
        latitude=model.latitude,
        longitude=model.longitude,
        arrival_at=model.arrival_at,
        departure_at=model.departure_at,
    )


def to_route_entity(model: RouteModel) -> Route:
    return Route(
        route_id=model.id,
        shipment_id=model.shipment_id,
        distance_km=float(model.distance_km),
        duration_minutes=model.duration_minutes,
        stops=list(model.stops or []),
        polyline=model.polyline,
        weather_factor=float(model.weather_factor),
        safety_score=float(model.safety_score),
        is_selected=model.is_selected,
        status=model.status_state,
        optimization_metadata=dict(model.optimization_metadata or {}),
        waypoints=[to_waypoint_entity(w) for w in model.waypoints],
        created_at=model.created_at,
        is_deleted=model.is_deleted,
        deleted_at=model.deleted_at,
    )
