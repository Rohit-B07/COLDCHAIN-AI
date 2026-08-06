"""Application wiring for dependency injection.

Concrete implementations are composed here and exposed as FastAPI dependencies.
Controllers declare only the abstract interfaces they need; the container is the
single place where concrete choices are made.
"""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.domain.repositories import (
    AlertRepository,
    ContainerRepository,
    DriverRepository,
    HealthRepository,
    PhCentreRepository,
    PredictionRepository,
    RefreshTokenRepository,
    RoleRepository,
    RouteRepository,
    ShipmentRepository,
    UserRepository,
    VehicleRepository,
    WarehouseRepository,
    WaypointRepository,
    WeatherCacheRepository,
)
from app.repositories.alert import SqlAlchemyAlertRepository
from app.repositories.facility import (
    SqlAlchemyPhCentreRepository,
    SqlAlchemyWarehouseRepository,
)
from app.repositories.health import SqlAlchemyHealthRepository
from app.repositories.logistics import (
    SqlAlchemyContainerRepository,
    SqlAlchemyDriverRepository,
    SqlAlchemyVehicleRepository,
)
from app.repositories.role import SqlAlchemyRoleRepository
from app.repositories.route import (
    SqlAlchemyRouteRepository,
    SqlAlchemyWaypointRepository,
)
from app.repositories.shipment import (
    SqlAlchemyPredictionRepository,
    SqlAlchemyShipmentRepository,
    SqlAlchemyWeatherCacheRepository,
)
from app.repositories.user import (
    SqlAlchemyRefreshTokenRepository,
    SqlAlchemyUserRepository,
)
from app.services.alert_service import AlertService
from app.services.auth_service import AuthService
from app.services.driver_service import DriverService
from app.services.intelligence_service import IntelligenceService
from app.services.phc_service import PhcService
from app.services.prediction_service import PredictionService
from app.services.route_service import RouteService
from app.services.shipment_service import ShipmentService
from app.services.user_service import UserService
from app.services.vehicle_service import VehicleService
from app.services.warehouse_service import WarehouseService
from app.use_cases.health import CheckHealth

DbSession = Annotated[AsyncSession, Depends(get_db)]


def get_health_repository(db: DbSession) -> HealthRepository:
    return SqlAlchemyHealthRepository(db)


def get_check_health(
    repo: Annotated[HealthRepository, Depends(get_health_repository)],
) -> CheckHealth:
    return CheckHealth(health_repo=repo)


def get_user_repository(db: DbSession) -> UserRepository:
    return SqlAlchemyUserRepository(db)


def get_refresh_token_repository(db: DbSession) -> RefreshTokenRepository:
    return SqlAlchemyRefreshTokenRepository(db)


def get_role_repository(db: DbSession) -> RoleRepository:
    return SqlAlchemyRoleRepository(db)


def get_warehouse_repository(db: DbSession) -> WarehouseRepository:
    return SqlAlchemyWarehouseRepository(db)


def get_phc_repository(db: DbSession) -> PhCentreRepository:
    return SqlAlchemyPhCentreRepository(db)


def get_driver_repository(db: DbSession) -> DriverRepository:
    return SqlAlchemyDriverRepository(db)


def get_vehicle_repository(db: DbSession) -> VehicleRepository:
    return SqlAlchemyVehicleRepository(db)


def get_container_repository(db: DbSession) -> ContainerRepository:
    return SqlAlchemyContainerRepository(db)


def get_shipment_repository(db: DbSession) -> ShipmentRepository:
    return SqlAlchemyShipmentRepository(db)


def get_route_repository(db: DbSession) -> RouteRepository:
    return SqlAlchemyRouteRepository(db)


def get_waypoint_repository(db: DbSession) -> WaypointRepository:
    return SqlAlchemyWaypointRepository(db)


def get_prediction_repository(db: DbSession) -> PredictionRepository:
    return SqlAlchemyPredictionRepository(db)


def get_weather_repository(db: DbSession) -> WeatherCacheRepository:
    return SqlAlchemyWeatherCacheRepository(db)


def get_alert_repository(db: DbSession) -> AlertRepository:
    return SqlAlchemyAlertRepository(db)


def get_auth_service(
    users: Annotated[UserRepository, Depends(get_user_repository)],
    tokens: Annotated[RefreshTokenRepository, Depends(get_refresh_token_repository)],
) -> AuthService:
    return AuthService(user_repo=users, token_repo=tokens)


def get_intelligence_service(
    prediction_repo: Annotated[PredictionRepository, Depends(get_prediction_repository)],
    shipment_repo: Annotated[ShipmentRepository, Depends(get_shipment_repository)],
    weather_repo: Annotated[WeatherCacheRepository, Depends(get_weather_repository)],
    alert_repo: Annotated[AlertRepository, Depends(get_alert_repository)],
) -> IntelligenceService:
    return IntelligenceService(
        prediction_repo=prediction_repo,
        shipment_repo=shipment_repo,
        weather_repo=weather_repo,
        alert_repo=alert_repo,
    )


def get_shipment_service(
    shipments: Annotated[ShipmentRepository, Depends(get_shipment_repository)],
    warehouses: Annotated[WarehouseRepository, Depends(get_warehouse_repository)],
    phcs: Annotated[PhCentreRepository, Depends(get_phc_repository)],
    containers: Annotated[ContainerRepository, Depends(get_container_repository)],
    drivers: Annotated[DriverRepository, Depends(get_driver_repository)],
) -> ShipmentService:
    return ShipmentService(
        shipment_repo=shipments,
        warehouse_repo=warehouses,
        phc_repo=phcs,
        container_repo=containers,
        driver_repo=drivers,
    )


def get_user_service(
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
) -> UserService:
    return UserService(user_repo=user_repo)


def get_warehouse_service(
    repo: Annotated[WarehouseRepository, Depends(get_warehouse_repository)],
) -> WarehouseService:
    return WarehouseService(warehouse_repo=repo)


def get_phc_service(
    repo: Annotated[PhCentreRepository, Depends(get_phc_repository)],
) -> PhcService:
    return PhcService(phc_repo=repo)


def get_driver_service(
    drivers: Annotated[DriverRepository, Depends(get_driver_repository)],
    vehicles: Annotated[VehicleRepository, Depends(get_vehicle_repository)],
) -> DriverService:
    return DriverService(driver_repo=drivers, vehicle_repo=vehicles)


def get_vehicle_service(
    repo: Annotated[VehicleRepository, Depends(get_vehicle_repository)],
) -> VehicleService:
    return VehicleService(vehicle_repo=repo)


def get_route_service(
    routes: Annotated[RouteRepository, Depends(get_route_repository)],
    waypoints: Annotated[WaypointRepository, Depends(get_waypoint_repository)],
    shipments: Annotated[ShipmentRepository, Depends(get_shipment_repository)],
) -> RouteService:
    return RouteService(
        route_repo=routes,
        waypoint_repo=waypoints,
        shipment_repo=shipments,
    )


def get_prediction_service(
    predictions: Annotated[PredictionRepository, Depends(get_prediction_repository)],
    shipments: Annotated[ShipmentRepository, Depends(get_shipment_repository)],
) -> PredictionService:
    return PredictionService(
        prediction_repo=predictions,
        shipment_repo=shipments,
    )


def get_alert_service(
    alerts: Annotated[AlertRepository, Depends(get_alert_repository)],
    shipments: Annotated[ShipmentRepository, Depends(get_shipment_repository)],
    containers: Annotated[ContainerRepository, Depends(get_container_repository)],
) -> AlertService:
    return AlertService(
        alert_repo=alerts,
        shipment_repo=shipments,
        container_repo=containers,
    )
