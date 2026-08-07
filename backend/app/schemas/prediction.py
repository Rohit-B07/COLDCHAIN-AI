"""Prediction DTOs: create, update, read and query filters."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

RiskLevelValue = Literal["low", "medium", "high", "critical"]


class PredictionCreate(BaseModel):
    shipment_id: UUID
    excursion_risk: float = Field(ge=0.0, le=1.0)
    risk_level: RiskLevelValue
    confidence: float = Field(ge=0.0, le=1.0)
    expected_min_temp: float = Field(default=2.0)
    expected_max_temp: float = Field(default=8.0)
    model_version: str = Field(default="rule-based-v1", min_length=1, max_length=64)
    features: dict = Field(default_factory=dict)
    explanations: dict = Field(default_factory=dict)

    @model_validator(mode="after")
    def _validate_temperature_range(self) -> "PredictionCreate":
        if self.expected_min_temp > self.expected_max_temp:
            raise ValueError("expected_min_temp must be <= expected_max_temp")
        return self


class PredictionUpdate(BaseModel):
    excursion_risk: float | None = Field(default=None, ge=0.0, le=1.0)
    risk_level: RiskLevelValue | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    expected_min_temp: float | None = None
    expected_max_temp: float | None = None
    model_version: str | None = Field(default=None, min_length=1, max_length=64)
    features: dict | None = None
    explanations: dict | None = None

    @model_validator(mode="after")
    def _validate_temperature_range(self) -> "PredictionUpdate":
        min_temp = self.expected_min_temp
        max_temp = self.expected_max_temp
        if min_temp is not None and max_temp is not None and min_temp > max_temp:
            raise ValueError("expected_min_temp must be <= expected_max_temp")
        return self


class PredictionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    shipment_id: UUID
    excursion_risk: float
    risk_level: RiskLevelValue
    confidence: float
    expected_min_temp: float
    expected_max_temp: float
    model_version: str
    features: dict
    explanations: dict
    created_at: datetime | None = None


class PredictionQueryParams(BaseModel):
    shipment_id: UUID | None = None
    risk_level: RiskLevelValue | None = None
    model_version: str | None = None
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)


class PredictionHistoryItem(BaseModel):
    """History-contract row for the prediction feed.

    A focused read model over a stored prediction: renames ``excursion_risk``
    to ``risk_score``, maps ``created_at`` to ``predicted_at`` and carries a
    derived, human-readable ``weather_summary``.
    """

    id: UUID
    shipment_id: UUID
    risk_score: float
    risk_level: RiskLevelValue
    confidence: float
    weather_summary: str
    predicted_at: datetime
    created_at: datetime


class PredictionHistoryQueryParams(BaseModel):
    shipment_id: UUID | None = None
    risk_level: RiskLevelValue | None = None
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)
