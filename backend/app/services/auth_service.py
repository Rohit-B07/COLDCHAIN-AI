"""Authentication service.

Coordinates password verification, token issuance, refresh and revocation.
Repository adapters are injected so the service stays free of persistence and
HTTP concerns.
"""

from uuid import UUID

from app.core.config import get_settings
from app.core.exceptions import (
    AuthenticationError,
    ConflictError,
    NotFoundError,
    TokenExpiredError,
)
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    refresh_token_expiry,
    verify_password,
)
from app.domain.entities.user import User
from app.domain.repositories import RefreshTokenRepository, UserRepository
from app.domain.value_objects import UserRole


class AuthService:
    def __init__(
        self,
        user_repo: UserRepository,
        token_repo: RefreshTokenRepository,
    ) -> None:
        self._user_repo = user_repo
        self._token_repo = token_repo

    async def register(
        self,
        email: str,
        full_name: str,
        password: str,
        role: UserRole = UserRole.LOGISTICS,
    ) -> User:
        existing = await self._user_repo.get_by_email(email)
        if existing is not None:
            raise ConflictError("An account with this email already exists")
        entity = User.create(
            email=email,
            full_name=full_name,
            password_hash=hash_password(password),
            role=role,
        )
        return await self._user_repo.create(entity)

    async def authenticate(self, email: str, password: str) -> User:
        user = await self._user_repo.get_by_email(email)
        if user is None or not verify_password(password, user.password_hash):
            raise AuthenticationError("Invalid credentials")
        if not user.is_active:
            raise AuthenticationError("Account is disabled")
        return user

    async def issue_tokens(self, user: User) -> dict:
        access = create_access_token(str(user.user_id), user.role.value)
        refresh = generate_refresh_token()
        await self._token_repo.create(
            user_id=user.user_id,
            token_hash=hash_refresh_token(refresh),
            expires_at=refresh_token_expiry(),
        )
        settings = get_settings()
        return {
            "access_token": access,
            "refresh_token": refresh,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }

    async def refresh(self, refresh_token: str) -> dict:
        token_hash = hash_refresh_token(refresh_token)
        if not await self._token_repo.is_valid(token_hash):
            raise TokenExpiredError("Refresh token is invalid or expired")
        user_id = await self._token_repo.get_user_id(token_hash)
        user = await self.get_user(user_id) if user_id else None
        if user is None:
            raise AuthenticationError("Refresh token is not associated with a user")
        await self._token_repo.revoke(token_hash)
        access = create_access_token(str(user.user_id), user.role.value)
        settings = get_settings()
        return {
            "access_token": access,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }

    async def logout(self, refresh_token: str) -> None:
        await self._token_repo.revoke(hash_refresh_token(refresh_token))

    async def get_user(self, user_id: UUID) -> User:
        user = await self._user_repo.get_by_id(user_id)
        if user is None:
            raise NotFoundError("User not found")
        return user
