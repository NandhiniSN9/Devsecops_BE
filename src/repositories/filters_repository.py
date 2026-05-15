"""Repository for client-facing lookup data access operations.

Consolidates specialization, status, and client queries into a single
repository since they all serve as filter/dropdown data for the frontend.
"""

import uuid

from sqlalchemy import String, distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.schema.project import Project
from src.repositories.schema.specialization import Specialization
from src.repositories.schema.status import Status
from src.settings import CLIENT_UUID_NAMESPACE


class ClientRepository:
    """Data access layer for client-facing lookup queries.

    Provides access to specializations, statuses, and clients
    used for filter dropdowns and lookup operations.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_active_specializations(self) -> list[Specialization]:
        """Return all specializations where is_active = 1."""
        stmt = select(Specialization).where(Specialization.is_active == 1)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_active_statuses(self) -> list[Status]:
        """Return all statuses where is_active = 1."""
        stmt = select(Status).where(Status.is_active == 1)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_active_clients(self) -> list[dict]:
        """Get distinct non-null, non-empty client values from active projects.

        Returns:
            List of dicts with 'client_id' (UUID v5) and 'client_name' keys,
            sorted alphabetically by client_name.
        """
        stmt = (
            select(distinct(Project.client))
            .where(Project.is_active == 1)
            .where(Project.client.isnot(None))
            .where(Project.client != "")
            .where(func.trim(Project.client.cast(String)) != "")
            .order_by(Project.client.asc())
        )

        result = await self._session.execute(stmt)
        rows = result.scalars().all()

        return [
            {
                "client_id": str(uuid.uuid5(CLIENT_UUID_NAMESPACE, client_name)),
                "client_name": client_name,
            }
            for client_name in rows
        ]
