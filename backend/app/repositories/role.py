"""SQLAlchemy async repository for roles.

Role lookups respect soft deletion by default: deleted roles are hidden unless
explicitly requested, preserving audit history while keeping the active role
catalog clean.
"""

import builtins
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.role import Role
from app.models.role import Role as RoleModel, user_roles
from app.repositories.base import to_role_entity


class SqlAlchemyRoleRepository:
    """Async-backed adapter for the Role aggregate."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, entity: Role) -> Role:
        self._session.add(
            RoleModel(
                id=entity.role_id,
                name=entity.name,
                description=entity.description,
                is_deleted=entity.is_deleted,
            )
        )
        await self._session.flush()
        return entity

    async def get(self, role_id: UUID) -> Role | None:
        result = await self._session.execute(
            select(RoleModel).where(RoleModel.id == role_id)
        )
        model = result.scalar_one_or_none()
        if model is None or model.is_deleted:
            return None
        return to_role_entity(model)

    async def get_by_name(self, name: str) -> Role | None:
        result = await self._session.execute(
            select(RoleModel).where(
                RoleModel.name == name.strip().lower(),
                RoleModel.is_deleted.is_(False),
            )
        )
        model = result.scalar_one_or_none()
        return to_role_entity(model) if model else None

    async def list(self, include_deleted: bool = False) -> list[Role]:
        query = select(RoleModel).order_by(RoleModel.name)
        if not include_deleted:
            query = query.where(RoleModel.is_deleted.is_(False))
        result = await self._session.execute(query)
        return [to_role_entity(model) for model in result.scalars().all()]

    async def get_roles_for_user(self, user_id: UUID) -> builtins.list[Role]:
        """Return the active roles currently assigned to a user."""
        result = await self._session.execute(
            select(RoleModel)
            .join(user_roles, user_roles.c.role_id == RoleModel.id)
            .where(
                user_roles.c.user_id == user_id,
                RoleModel.is_deleted.is_(False),
            )
            .order_by(RoleModel.name)
        )
        return [to_role_entity(model) for model in result.scalars().all()]

    async def soft_delete(self, role_id: UUID) -> Role | None:
        result = await self._session.execute(
            select(RoleModel).where(RoleModel.id == role_id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        model.is_deleted = True
        await self._session.flush()
        return to_role_entity(model)
