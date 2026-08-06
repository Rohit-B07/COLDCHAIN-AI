"""Health repository backed by SQLAlchemy async."""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.repositories import HealthRepository


class SqlAlchemyHealthRepository(HealthRepository):
    """Executes a trivial query through the provided async session."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def ping(self) -> bool:
        try:
            await self._session.execute(text("SELECT 1"))
            return True
        except Exception:
            return False
