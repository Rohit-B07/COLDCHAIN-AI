"""Prediction endpoints: CRUD, history and risk-level filtering."""

from typing import Annotated, cast
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.deps.container import (
    get_prediction_history_service,
    get_prediction_service,
)
from app.api.deps.rbac import require_permissions
from app.domain.entities.intelligence import Prediction
from app.domain.permissions import Permission
from app.schemas.common import ApiResponse, Page
from app.schemas.prediction import (
    PredictionCreate,
    PredictionHistoryItem,
    PredictionHistoryQueryParams,
    PredictionQueryParams,
    PredictionRead,
    PredictionUpdate,
    RiskLevelValue,
)
from app.services.prediction_history_service import PredictionHistoryService
from app.services.prediction_service import PredictionService

router = APIRouter(prefix="/predictions", tags=["predictions"])

_ViewPredictions = Depends(require_permissions(Permission.PREDICTION_VIEW))
_ManagePredictions = Depends(require_permissions(Permission.PREDICTION_MANAGE))


def _read(prediction: Prediction) -> PredictionRead:
    return PredictionRead(
        id=prediction.prediction_id,
        shipment_id=prediction.shipment_id,
        excursion_risk=prediction.excursion_risk,
        risk_level=cast(RiskLevelValue, prediction.risk_level),
        confidence=prediction.confidence,
        expected_min_temp=prediction.expected_min_temp,
        expected_max_temp=prediction.expected_max_temp,
        model_version=prediction.model_version,
        features=prediction.features,
        explanations=prediction.explanations,
        created_at=prediction.created_at,
    )


@router.get(
    "",
    response_model=ApiResponse[Page[PredictionRead]],
    summary="List predictions (paginated and filtered)",
    dependencies=[_ViewPredictions],
)
async def list_predictions(
    params: Annotated[PredictionQueryParams, Query()],
    service: Annotated[PredictionService, Depends(get_prediction_service)],
) -> ApiResponse[Page[PredictionRead]]:
    items, total = await service.list(
        shipment_id=params.shipment_id,
        risk_level=params.risk_level,
        model_version=params.model_version,
        page=params.page,
        size=params.size,
    )
    pages = (total + params.size - 1) // params.size if total else 0
    return ApiResponse(
        data=Page[PredictionRead](
            items=[_read(prediction) for prediction in items],
            total=total,
            page=params.page,
            size=params.size,
            pages=pages,
        )
    )


@router.get(
    "/history",
    response_model=ApiResponse[Page[PredictionHistoryItem]],
    summary="List prediction history (paginated and filtered)",
    dependencies=[_ViewPredictions],
)
async def list_prediction_history(
    params: Annotated[PredictionHistoryQueryParams, Query()],
    service: Annotated[
        PredictionHistoryService, Depends(get_prediction_history_service)
    ],
) -> ApiResponse[Page[PredictionHistoryItem]]:
    items, total = await service.list(
        shipment_id=params.shipment_id,
        risk_level=params.risk_level,
        page=params.page,
        size=params.size,
    )
    pages = (total + params.size - 1) // params.size if total else 0
    return ApiResponse(
        data=Page[PredictionHistoryItem](
            items=items,
            total=total,
            page=params.page,
            size=params.size,
            pages=pages,
        )
    )


@router.post(
    "",
    response_model=ApiResponse[PredictionRead],
    status_code=201,
    summary="Record a risk prediction for a shipment",
    dependencies=[_ManagePredictions],
)
async def create_prediction(
    payload: PredictionCreate,
    service: Annotated[PredictionService, Depends(get_prediction_service)],
) -> ApiResponse[PredictionRead]:
    entity = await service.create(payload)
    return ApiResponse(data=_read(entity))


@router.get(
    "/{prediction_id}",
    response_model=ApiResponse[PredictionRead],
    summary="Get a prediction by id",
    dependencies=[_ViewPredictions],
)
async def get_prediction(
    prediction_id: UUID,
    service: Annotated[PredictionService, Depends(get_prediction_service)],
) -> ApiResponse[PredictionRead]:
    entity = await service.get(prediction_id)
    return ApiResponse(data=_read(entity))


@router.patch(
    "/{prediction_id}",
    response_model=ApiResponse[PredictionRead],
    summary="Update a prediction's metrics",
    dependencies=[_ManagePredictions],
)
async def update_prediction(
    prediction_id: UUID,
    payload: PredictionUpdate,
    service: Annotated[PredictionService, Depends(get_prediction_service)],
) -> ApiResponse[PredictionRead]:
    entity = await service.update(prediction_id, payload)
    return ApiResponse(data=_read(entity))


@router.delete(
    "/{prediction_id}",
    response_model=ApiResponse[PredictionRead],
    summary="Delete a prediction",
    dependencies=[_ManagePredictions],
)
async def delete_prediction(
    prediction_id: UUID,
    service: Annotated[PredictionService, Depends(get_prediction_service)],
) -> ApiResponse[PredictionRead]:
    entity = await service.delete(prediction_id)
    return ApiResponse(data=_read(entity))


@router.get(
    "/shipments/{shipment_id}/history",
    response_model=ApiResponse[list[PredictionRead]],
    summary="List prediction history for a shipment",
    dependencies=[_ViewPredictions],
)
async def prediction_history(
    shipment_id: UUID,
    service: Annotated[PredictionService, Depends(get_prediction_service)],
) -> ApiResponse[list[PredictionRead]]:
    predictions = await service.history(shipment_id)
    return ApiResponse(data=[_read(prediction) for prediction in predictions])
