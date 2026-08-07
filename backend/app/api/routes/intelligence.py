"""Intelligence endpoints: excursion predictions, route optimisation and alerts."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.deps.auth import CurrentUser
from app.api.deps.container import (
    get_intelligence_service,
    get_prediction_repository,
    get_shipment_service,
)
from app.api.deps.rbac import require_permissions
from app.core.exceptions import NotFoundError
from app.domain.permissions import Permission
from app.domain.repositories import PredictionRepository
from app.schemas.common import ApiResponse
from app.schemas.intelligence import (
    AlertCreate,
    AlertRead,
    PredictionRead,
    RouteRead,
)
from app.schemas.shipment import AlertsOutcome
from app.services.intelligence_service import IntelligenceService
from app.services.shipment_service import ShipmentService

router = APIRouter(tags=["intelligence"])

prediction_router = APIRouter(prefix="/shipments/{shipment_id}/prediction")
route_router = APIRouter(prefix="/shipments/{shipment_id}/route")
alert_router = APIRouter(prefix="/alerts")

_ViewPredictions = Depends(require_permissions(Permission.PREDICTION_VIEW))
_ManagePredictions = Depends(require_permissions(Permission.PREDICTION_MANAGE))


@prediction_router.get(
    "",
    response_model=ApiResponse[PredictionRead],
    summary="Get the latest risk prediction",
    dependencies=[_ViewPredictions],
)
async def get_prediction(
    shipment_id: UUID,
    prediction_repo: Annotated[PredictionRepository, Depends(get_prediction_repository)],
) -> ApiResponse[PredictionRead]:
    prediction = await prediction_repo.latest_for_shipment(shipment_id)
    if prediction is None:
        raise NotFoundError("No prediction found for this shipment")
    return ApiResponse(
        data=PredictionRead(
            id=prediction.prediction_id,
            shipment_id=prediction.shipment_id,
            excursion_risk=prediction.excursion_risk,
            risk_level=prediction.risk_level,
            confidence=prediction.confidence,
            expected_min_temp=prediction.expected_min_temp,
            expected_max_temp=prediction.expected_max_temp,
            model_version=prediction.model_version,
            features=prediction.features,
            explanations=prediction.explanations,
            created_at=prediction.created_at,
        )
    )


@prediction_router.post(
    "",
    response_model=ApiResponse[PredictionRead],
    summary="Compute a fresh excursion risk prediction",
    dependencies=[_ManagePredictions],
)
async def create_prediction(
    shipment_id: UUID,
    intelligence: Annotated[IntelligenceService, Depends(get_intelligence_service)],
    shipments: Annotated[ShipmentService, Depends(get_shipment_service)],
) -> ApiResponse[PredictionRead]:
    shipment = await shipments.get(shipment_id)
    prediction = await intelligence.predict_excursion_risk(shipment)
    return ApiResponse(
        data=PredictionRead(
            id=prediction.prediction_id,
            shipment_id=prediction.shipment_id,
            excursion_risk=prediction.excursion_risk,
            risk_level=prediction.risk_level,
            confidence=prediction.confidence,
            expected_min_temp=prediction.expected_min_temp,
            expected_max_temp=prediction.expected_max_temp,
            model_version=prediction.model_version,
            features=prediction.features,
            explanations=prediction.explanations,
            created_at=prediction.created_at,
        )
    )


@route_router.get(
    "",
    response_model=ApiResponse[RouteRead],
    summary="Plan the safest dispatch route for a shipment",
)
async def plan_route(
    shipment_id: UUID,
    intelligence: Annotated[IntelligenceService, Depends(get_intelligence_service)],
    shipments: Annotated[ShipmentService, Depends(get_shipment_service)],
) -> ApiResponse[RouteRead]:
    shipment = await shipments.get(shipment_id)
    origin = (18.9388, 72.8355)  # placeholder warehouse coordinate
    destination = (19.0760, 72.8777)  # placeholder PHC coordinate
    route = await intelligence.plan_route(shipment, origin, destination)
    return ApiResponse(
        data=RouteRead(
            id=route.route_id,
            shipment_id=route.shipment_id,
            distance_km=route.distance_km,
            duration_minutes=route.duration_minutes,
            stops=route.stops,
            polyline=route.polyline,
            weather_factor=route.weather_factor,
            safety_score=route.safety_score,
            is_selected=route.is_selected,
        )
    )


@alert_router.get("", response_model=ApiResponse[list[AlertRead]], summary="List cold-chain alerts")
async def list_alerts(
    intelligence: Annotated[IntelligenceService, Depends(get_intelligence_service)],
    status: str | None = Query(default=None),
) -> ApiResponse[list[AlertRead]]:
    alerts = await intelligence.list_alerts(status=status)
    return ApiResponse(
        data=[
            AlertRead(
                id=a.alert_id,
                shipment_id=a.shipment_id,
                container_id=a.container_id,
                severity=a.severity,
                alert_type=a.alert_type,
                message=a.message,
                status=a.status,
                acknowledged_by=None,
                acknowledged_at=None,
                created_at=None,
            )
            for a in alerts
        ]
    )


@alert_router.post(
    "",
    response_model=ApiResponse[AlertsOutcome],
    status_code=201,
    summary="Raise an alert (prototype helper)",
)
async def raise_alert(
    payload: AlertCreate,
    intelligence: Annotated[IntelligenceService, Depends(get_intelligence_service)],
) -> ApiResponse[AlertsOutcome]:
    await intelligence.raise_alert(
        severity=payload.severity,
        alert_type=payload.alert_type,
        message=payload.message,
        shipment_id=payload.shipment_id,
        container_id=payload.container_id,
    )
    return ApiResponse(data=AlertsOutcome(alerts=[payload.message]))


@alert_router.post(
    "/{alert_id}/acknowledge",
    response_model=ApiResponse[AlertRead],
    summary="Acknowledge an alert",
)
async def acknowledge_alert(
    alert_id: UUID,
    user: CurrentUser,
    intelligence: Annotated[IntelligenceService, Depends(get_intelligence_service)],
) -> ApiResponse[AlertRead]:
    alert = await intelligence.acknowledge_alert(alert_id, user.user_id)
    return ApiResponse(
        data=AlertRead(
            id=alert.alert_id,
            shipment_id=alert.shipment_id,
            container_id=alert.container_id,
            severity=alert.severity,
            alert_type=alert.alert_type,
            message=alert.message,
            status=alert.status,
            acknowledged_by=user.user_id,
            acknowledged_at=None,
            created_at=None,
        )
    )
