"""Shared response envelope.

Standardising the envelope used by every API response keeps the client
contract consistent and extensible (metadata, tracing, pagination later).
"""

from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """Uniform success envelope."""

    success: bool = True
    data: T | None = None


class Page(BaseModel, Generic[T]):
    """Uniform pagination envelope."""

    items: list[T]
    total: int
    page: int
    size: int
    pages: int


class ErrorDetail(BaseModel):
    """Single structured error item."""

    field: str | None = None
    message: str


class ApiErrorResponse(BaseModel):
    """Uniform error envelope."""

    success: bool = False
    error_code: str
    message: str
    details: list[ErrorDetail] = []
