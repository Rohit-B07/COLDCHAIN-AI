"""Application exceptions.

Domain-level exceptions that map cleanly onto HTTP responses in the global
exception handler. Keeping them here lets the application layer raise rich,
explicit errors without importing HTTP libraries.
"""

from typing import Any


class AppError(Exception):
    """Base class for expected application errors."""

    status_code: int = 400
    error_code: str = "app_error"

    def __init__(self, message: str, details: list[dict[str, Any]] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or []


class NotFoundError(AppError):
    status_code = 404
    error_code = "not_found"


class AuthenticationError(AppError):
    status_code = 401
    error_code = "authentication_failed"


class TokenExpiredError(AuthenticationError):
    error_code = "token_expired"


class AuthorizationError(AppError):
    status_code = 403
    error_code = "forbidden"


class ConflictError(AppError):
    status_code = 409
    error_code = "conflict"


class ValidationError(AppError):
    status_code = 422
    error_code = "validation_error"


class BadRequestError(AppError):
    status_code = 400
    error_code = "bad_request"
