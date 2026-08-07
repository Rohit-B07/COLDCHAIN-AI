"""Auth dependencies: current-user resolution and RBAC guard.

Uses an HTTP bearer security scheme: Swagger's *Authorize* dialog stores a
bearer token and protected routes read ``Authorization: Bearer``. The scheme is
declared as plain HTTP bearer (not OAuth2 password flow) because the token
endpoint returns an enveloped response that Swagger's OAuth2 client cannot
parse; bearer auth attaches the header directly.
"""

from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError

from app.api.deps.container import get_user_repository
from app.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    TokenExpiredError,
)
from app.core.security import decode_token, subject_to_uuid
from app.domain.entities.user import User
from app.domain.repositories import UserRepository


class _BearerToken(HTTPBearer):
    """HTTP bearer scheme that yields the raw token string.

    ``HTTPBearer`` returns ``HTTPAuthorizationCredentials``; subclasses it to
    hand back just the token so downstream code keeps receiving ``str | None``.
    """

    async def __call__(self, request: Request) -> str | None:  # type: ignore[override]
        credentials: HTTPAuthorizationCredentials | None = await super().__call__(
            request
        )
        return credentials.credentials if credentials is not None else None


oauth2_scheme = _BearerToken(auto_error=False)


async def get_current_user(
    token: Annotated[str | None, Depends(oauth2_scheme)],
    users: Annotated[UserRepository, Depends(get_user_repository)],
) -> User:
    if token is None:
        raise AuthenticationError("Missing bearer token")
    try:
        payload = decode_token(token)
    except InvalidTokenError as exc:
        raise TokenExpiredError("Token is invalid or expired") from exc
    if payload.get("type") != "access":
        raise TokenExpiredError("Token is not an access token")

    user_id = subject_to_uuid(token)
    user = await users.get_by_id(user_id)
    if user is None or not user.is_active:
        raise AuthenticationError("Account no longer valid")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


class RequireRoles:
    """Dependency factory enforcing role-based access control."""

    def __init__(self, *roles: str) -> None:
        self._roles = set(roles)

    def __call__(self, user: CurrentUser) -> User:
        if user.role.value not in self._roles:
            raise AuthorizationError("You do not have permission to perform this action")
        return user
