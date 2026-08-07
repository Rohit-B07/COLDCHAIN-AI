"""Async database seeder: default roles, permissions and initial admin user.

Idempotent by design — running it multiple times never duplicates rows:

* Roles are created only when a role with the same name is missing.
* Permissions are code constants (``app.domain.permissions``) so they are
  inherently defined once; the seeder validates the catalog but inserts no
  permission rows.
* The initial admin user is created only when its email is not already present
  (and is linked to the ``admin`` role via ``user_roles``).

Usage:

    python -m app.seed
"""

import asyncio
import logging
import sys
from collections.abc import Callable, Coroutine
from typing import TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.session import session_scope
from app.domain.entities.role import Role
from app.domain.permissions import DEFAULT_ROLES, ROLE_DESCRIPTIONS
from app.domain.value_objects import UserRole
from app.models.role import Role as RoleModel
from app.models.user import User as UserModel
from app.repositories.role import SqlAlchemyRoleRepository

logger = logging.getLogger("coldchain.seed")


async def seed_roles(session: AsyncSession) -> int:
    """Create default roles only if they do not already exist.

    Returns the number of roles inserted.
    """
    role_repo = SqlAlchemyRoleRepository(session)
    created = 0
    for name in DEFAULT_ROLES:
        if await role_repo.get_by_name(name) is not None:
            continue
        role = Role.create(name=name, description=ROLE_DESCRIPTIONS[name])
        await role_repo.create(role)
        created += 1
        logger.info("Seeded role %r", name)
    return created


async def seed_admin(session: AsyncSession) -> int:
    """Create the bootstrap admin user if its email is absent.

    The legacy reserved-domain address ``admin@coldchain.local`` is renamed to
    the current ``SEED_ADMIN_EMAIL`` when found, so an existing database carries
    the fix forward instead of requiring manual data repair.

    Returns 1 when the user was created or renamed, 0 when it already existed.
    """
    settings = get_settings()
    email = settings.SEED_ADMIN_EMAIL.strip().lower()

    result = await session.execute(
        select(UserModel)
        .options(selectinload(UserModel.roles))
        .where(UserModel.email == email, UserModel.is_deleted.is_(False))
    )
    if result.scalar_one_or_none() is not None:
        return 0

    legacy_email = "admin@coldchain.local"
    if email != legacy_email:
        legacy = (
            await session.execute(
                select(UserModel)
                .options(selectinload(UserModel.roles))
                .where(UserModel.email == legacy_email, UserModel.is_deleted.is_(False))
            )
        ).scalar_one_or_none()
        if legacy is not None:
            legacy.email = email
            logger.info("Renamed seeded admin user %r -> %r", legacy_email, email)
            return 1

    admin_role = (
        await session.execute(
            select(RoleModel).where(
                RoleModel.name == "admin", RoleModel.is_deleted.is_(False)
            )
        )
    ).scalar_one_or_none()

    user = UserModel(
        email=email,
        full_name=settings.SEED_ADMIN_FULL_NAME,
        password_hash=hash_password(settings.SEED_ADMIN_PASSWORD),
        role=UserRole.SUPER_ADMIN.value,
        is_active=True,
        is_deleted=False,
        roles=[admin_role] if admin_role is not None else [],
    )
    session.add(user)
    logger.info("Seeded initial admin user %r", email)
    return 1


async def seed() -> None:
    """Run the full seeding routine inside a single transaction."""
    async with session_scope() as session:
        created_roles = await seed_roles(session)
        created_admins = await seed_admin(session)
    logger.info(
        "Seed complete: %d role(s) and %d admin user(s) created",
        created_roles,
        created_admins,
    )


_T = TypeVar("_T")


def run_async(coro: Callable[[], Coroutine[object, object, _T]]) -> _T:
    """Run an async entry-point on a psycopg-compatible event loop.

    ``psycopg`` async mode cannot run on Windows' default ``ProactorEventLoop``,
    so the selector loop policy is installed explicitly on that platform.
    """
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    return asyncio.run(coro())


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    run_async(seed)


if __name__ == "__main__":
    main()
