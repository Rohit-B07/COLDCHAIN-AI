"""Prediction history service: paginated, filterable read model.

Reuses the existing prediction read path (pagination and filtering live in
``PredictionService`` and the repository) and only adds the history-specific
presentation mapping, so there is no duplicated SQL for the feed.
"""

import builtins
from datetime import UTC, datetime
from typing import cast
from uuid import UUID

from app.domain.entities.intelligence import Prediction
from app.schemas.prediction import PredictionHistoryItem, RiskLevelValue
from app.services.prediction_service import PredictionService


def _weather_summary(explanations: dict) -> str:
    """Derive a human-readable weather note from the rule explanations."""
    for rule in explanations.get("rules") or []:
        if rule.get("name") == "ambient_temperature_delta":
            detail = rule.get("detail")
            if detail:
                return str(detail)
    return "Rule-based temperature-excursion prediction"


def to_history_item(prediction: Prediction) -> PredictionHistoryItem:
    """Map a stored prediction to its history-contract representation."""
    predicted_at = prediction.created_at or datetime.now(UTC)
    return PredictionHistoryItem(
        id=prediction.prediction_id,
        shipment_id=prediction.shipment_id,
        risk_score=prediction.excursion_risk,
        risk_level=cast(RiskLevelValue, prediction.risk_level),
        confidence=prediction.confidence,
        weather_summary=_weather_summary(prediction.explanations),
        predicted_at=predicted_at,
        created_at=predicted_at,
    )


class PredictionHistoryService:
    """Business wrapper for the prediction history feed."""

    def __init__(self, prediction_service: PredictionService) -> None:
        self._service = prediction_service

    async def list(
        self,
        *,
        shipment_id: UUID | None = None,
        risk_level: str | None = None,
        page: int = 1,
        size: int = 20,
    ) -> tuple[builtins.list[PredictionHistoryItem], int]:
        items, total = await self._service.list(
            shipment_id=shipment_id,
            risk_level=risk_level,
            page=page,
            size=size,
        )
        return [to_history_item(item) for item in items], total
