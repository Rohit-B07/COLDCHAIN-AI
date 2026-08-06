"""Global exception handlers.

Registers uniform handlers for domain errors, request validation failures and
unexpected exceptions so every response follows the same structured envelope.
"""

import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.exceptions import AppError
from app.schemas.common import ApiErrorResponse, ErrorDetail

logger = logging.getLogger("coldchain_api.errors")


def register_exception_handlers(app: FastAPI) -> None:
    """Attach all application exception handlers to the FastAPI app."""

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        detail = [
            ErrorDetail(field=d.get("field"), message=d.get("message", ""))
            for d in exc.details
            if isinstance(d, dict)
        ]
        return JSONResponse(
            status_code=exc.status_code,
            content=ApiErrorResponse(
                error_code=exc.error_code,
                message=exc.message,
                details=detail,
            ).model_dump(),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        details = [
            ErrorDetail(
                field=".".join(str(part) for part in (err.get("loc") or [])),
                message=err.get("msg", "invalid value"),
            )
            for err in exc.errors()
        ]
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=ApiErrorResponse(
                error_code="validation_error",
                message="Request validation failed",
                details=details,
            ).model_dump(),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception while handling %s %s", request.method, request.url)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ApiErrorResponse(
                error_code="internal_error",
                message="An unexpected error occurred",
            ).model_dump(),
        )
