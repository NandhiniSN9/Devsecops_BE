"""Repository for status data access operations."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.schema.status import Status


class StatusRepository:
    """Data access layer for the statuses table."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_active_statuses(self) -> list[Status]:
        """Return all statuses where is_active = 1."""
        stmt = select(Status).where(Status.is_active == 1)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
