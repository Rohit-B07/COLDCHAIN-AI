"""User management service.

Coordinates profile reads/updates, password changes and account lifecycle
(activate/deactivate) plus paginated, filtered user listing. Repository
adapters are injected so the service stays free of persistence and HTTP
concerns.
"""

from uuid import UUID

from app.core.exceptions import BadRequestError, ConflictError, NotFoundError
from app.core.security import hash_password, verify_password
from app.domain.entities.user import User
from app.domain.repositories import UserRepository
from app.domain.value_objects import UserRole


class UserService:
    def __init__(self, user_repo: UserRepository) -> None:
        self._user_repo = user_repo

    async def get_profile(self, user_id: UUID) -> User:
        user = await self._user_repo.get_by_id(user_id)
        if user is None:
            raise NotFoundError("User not found")
        return user

    async def update_profile(
        self,
        user_id: UUID,
        full_name: str | None,
        email: str | None,
    ) -> User:
        user = await self.get_profile(user_id)
        if email is not None and email.strip().lower() != user.email:
            existing = await self._user_repo.get_by_email(email)
            if existing is not None and existing.user_id != user.user_id:
                raise ConflictError("Email is already in use")
        user.update_profile(full_name=full_name, email=email)
        return await self._user_repo.update(user)

    async def change_password(
        self,
        user_id: UUID,
        current_password: str,
        new_password: str,
    ) -> None:
        user = await self.get_profile(user_id)
        if not verify_password(current_password, user.password_hash):
            raise BadRequestError("Current password is incorrect")
        if verify_password(new_password, user.password_hash):
            raise BadRequestError("New password must differ from the current password")
        user.change_password(hash_password(new_password))
        await self._user_repo.update(user)

    async def list_users(
        self,
        *,
        search: str | None,
        role: UserRole | None,
        is_active: bool | None,
        page: int,
        size: int,
    ) -> tuple[list[User], int]:
        offset = (page - 1) * size
        role_name = role.value if role is not None else None
        total = await self._user_repo.count(
            search=search,
            role=role_name,
            is_active=is_active,
        )
        items = await self._user_repo.list_paginated(
            search=search,
            role=role_name,
            is_active=is_active,
            offset=offset,
            limit=size,
        )
        return items, total

    async def deactivate(self, user_id: UUID, actor_id: UUID) -> User:
        if user_id == actor_id:
            raise BadRequestError("You cannot deactivate your own account")
        return await self._set_active(user_id, active=False)

    async def activate(self, user_id: UUID) -> User:
        return await self._set_active(user_id, active=True)

    async def _set_active(self, user_id: UUID, active: bool) -> User:
        user = await self.get_profile(user_id)
        if active and not user.is_active:
            user.activate()
        elif not active and user.is_active:
            user.deactivate()
        return await self._user_repo.update(user)
