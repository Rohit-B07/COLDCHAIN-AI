"""SQLAlchemy async repositories for users and refresh tokens."""

import builtins
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.domain.entities.user import User
from app.models.user import (
    RefreshToken as RefreshTokenModel,
    User as UserModel,
    UserRole as UserRoleModel,
)
from app.repositories.base import to_user_entity


class SqlAlchemyUserRepository:
    """Async user persistence."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, entity: User) -> User:
        model = UserModel(
            id=entity.user_id,
            email=entity.email,
            full_name=entity.full_name,
            password_hash=entity.password_hash,
            role=entity.role.value,
            is_active=entity.is_active,
        )
        self._session.add(model)
        await self._session.flush()
        return entity

    async def update(self, entity: User) -> User:
        model = await self._session.get(UserModel, entity.user_id)
        if model is None:
            raise NotFoundError("User not found")
        model.full_name = entity.full_name
        model.email = entity.email
        model.password_hash = entity.password_hash
        model.role = UserRoleModel(entity.role.value)
        model.is_active = entity.is_active
        await self._session.flush()
        return entity

    async def get_by_id(self, user_id: UUID) -> User | None:
        result = await self._session.execute(
            select(UserModel).where(UserModel.id == user_id)
        )
        model = result.scalar_one_or_none()
        return to_user_entity(model) if model else None

    async def get_by_email(self, email: str) -> User | None:
        result = await self._session.execute(
            select(UserModel).where(UserModel.email == email.lower().strip())
        )
        model = result.scalar_one_or_none()
        return to_user_entity(model) if model else None

    async def list(self) -> builtins.list[User]:
        result = await self._session.execute(select(UserModel).order_by(UserModel.created_at))
        return [to_user_entity(model) for model in result.scalars().all()]

    async def count(
        self,
        *,
        search: str | None = None,
        role: str | None = None,
        is_active: bool | None = None,
    ) -> int:
        query = self._apply_filters(
            select(func.count(UserModel.id)), search=search, role=role, is_active=is_active
        ).where(UserModel.is_deleted.is_(False))
        result = await self._session.execute(query)
        return int(result.scalar_one())

    async def list_paginated(
        self,
        *,
        search: str | None = None,
        role: str | None = None,
        is_active: bool | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> builtins.list[User]:
        query = self._apply_filters(
            select(UserModel), search=search, role=role, is_active=is_active
        ).where(UserModel.is_deleted.is_(False))
        query = query.order_by(UserModel.created_at.desc()).offset(offset).limit(limit)
        result = await self._session.execute(query)
        return [to_user_entity(model) for model in result.scalars().all()]

    def _apply_filters(
        self,
        query: Select,
        *,
        search: str | None,
        role: str | None,
        is_active: bool | None,
    ) -> Select:
        if search:
            pattern = f"%{search.strip().lower()}%"
            query = query.where(
                or_(
                    UserModel.email.ilike(pattern),
                    UserModel.full_name.ilike(pattern),
                )
            )
        if role:
            query = query.where(UserModel.role == role)
        if is_active is not None:
            query = query.where(UserModel.is_active.is_(is_active))
        return query


class SqlAlchemyRefreshTokenRepository:
    """Async-backed adapter for opaque refresh tokens."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, user_id: UUID, token_hash: str, expires_at: datetime) -> None:
        self._session.add(
            RefreshTokenModel(
                user_id=user_id,
                token_hash=token_hash,
                expires_at=expires_at,
            )
        )
        await self._session.flush()

    async def revoke(self, token_hash: str) -> None:
        result = await self._session.execute(
            select(RefreshTokenModel).where(RefreshTokenModel.token_hash == token_hash)
        )
        token = result.scalar_one_or_none()
        if token is not None and token.revoked_at is None:
            token.revoked_at = datetime.now(UTC)
            await self._session.flush()

    async def is_valid(self, token_hash: str) -> bool:
        result = await self._session.execute(
            select(RefreshTokenModel).where(RefreshTokenModel.token_hash == token_hash)
        )
        token = result.scalar_one_or_none()
        if token is None or token.revoked_at is not None:
            return False
        return token.expires_at > datetime.now(UTC)

    async def get_user_id(self, token_hash: str) -> UUID | None:
        result = await self._session.execute(
            select(RefreshTokenModel).where(RefreshTokenModel.token_hash == token_hash)
        )
        token = result.scalar_one_or_none()
        return token.user_id if token is not None else None
