"""Repository for specialization data access operations."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.schema.specialization import Specialization


class SpecializationRepository:
    """Data access layer for the specializations table."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_active_specializations(self) -> list[Specialization]:
        """Return all specializations where is_active = 1."""
        stmt = select(Specialization).where(Specialization.is_active == 1)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
