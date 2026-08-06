"""Prediction service: CRUD and history for shipment risk predictions."""

import builtins
from uuid import UUID

from app.core.exceptions import NotFoundError, ValidationError
from app.domain.entities.intelligence import Prediction
from app.domain.repositories import PredictionRepository, ShipmentRepository
from app.schemas.prediction import PredictionCreate, PredictionUpdate


class PredictionService:
    def __init__(
        self,
        prediction_repo: PredictionRepository,
        shipment_repo: ShipmentRepository,
    ) -> None:
        self._predictions = prediction_repo
        self._shipments = shipment_repo

    async def create(self, payload: PredictionCreate) -> Prediction:
        shipment = await self._shipments.get(payload.shipment_id)
        if shipment is None:
            raise NotFoundError("Shipment not found")
        try:
            entity = Prediction.create(
                shipment_id=payload.shipment_id,
                excursion_risk=payload.excursion_risk,
                risk_level=payload.risk_level,
                confidence=payload.confidence,
                expected_min_temp=payload.expected_min_temp,
                expected_max_temp=payload.expected_max_temp,
                model_version=payload.model_version,
                features=payload.features,
                explanations=payload.explanations,
            )
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        return await self._predictions.create(entity)

    async def get(self, prediction_id: UUID) -> Prediction:
        entity = await self._predictions.get(prediction_id)
        if entity is None:
            raise NotFoundError("Prediction not found")
        return entity

    async def list(
        self,
        *,
        shipment_id: UUID | None = None,
        risk_level: str | None = None,
        model_version: str | None = None,
        page: int = 1,
        size: int = 20,
    ) -> tuple[builtins.list[Prediction], int]:
        offset = (page - 1) * size
        items = await self._predictions.list_paginated(
            shipment_id=shipment_id,
            risk_level=risk_level,
            model_version=model_version,
            offset=offset,
            limit=size,
        )
        total = await self._predictions.count(
            shipment_id=shipment_id,
            risk_level=risk_level,
            model_version=model_version,
        )
        return items, total

    async def history(self, shipment_id: UUID) -> builtins.list[Prediction]:
        shipment = await self._shipments.get(shipment_id)
        if shipment is None:
            raise NotFoundError("Shipment not found")
        return await self._predictions.list_for_shipment(shipment_id)

    async def update(self, prediction_id: UUID, payload: PredictionUpdate) -> Prediction:
        entity = await self.get(prediction_id)
        try:
            entity.update(
                excursion_risk=payload.excursion_risk,
                risk_level=payload.risk_level,
                confidence=payload.confidence,
                expected_min_temp=payload.expected_min_temp,
                expected_max_temp=payload.expected_max_temp,
                model_version=payload.model_version,
                features=payload.features,
                explanations=payload.explanations,
            )
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        return await self._predictions.update(entity)

    async def delete(self, prediction_id: UUID) -> Prediction:
        entity = await self.get(prediction_id)
        deleted = await self._predictions.delete(prediction_id)
        if deleted is None:
            raise NotFoundError("Prediction not found")
        return entity
