"""Repository for project-related database operations."""

import uuid

from sqlalchemy import String, case, distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.schema.devsecops_ticket import DevsecopsTicket
from src.repositories.schema.project import Project
from src.repositories.schema.status import Status


class ProjectRepository:
    """Data access layer for project queries."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_status_distribution(self, specialization_ids: list[uuid.UUID] | None) -> list[dict]:
        """Get project count distribution grouped by status.

        Uses LEFT JOIN from statuses to projects to include statuses with 0 projects.
        When specialization_ids is provided, additionally joins devsecops_tickets
        to filter projects by specialization.

        Args:
            specialization_ids: Optional list of specialization UUIDs to filter by.

        Returns:
            List of dicts with 'status_name' and 'count' keys, ordered by status_name ASC.
        """
        if specialization_ids:
            # With specialization filter: LEFT JOIN statuses → projects → devsecops_tickets
            # Only count projects that have a matching ticket with the given specialization.
            # Uses CASE expression to only count project_id when a matching ticket exists.
            stmt = (
                select(
                    Status.status_name,
                    func.count(
                        distinct(
                            case(
                                (DevsecopsTicket.ticket_id.isnot(None), Project.project_id),
                                else_=None,
                            )
                        )
                    ).label("count"),
                )
                .select_from(Status)
                .outerjoin(
                    Project,
                    (Project.status_id == Status.status_id) & (Project.is_active == 1),
                )
                .outerjoin(
                    DevsecopsTicket,
                    (DevsecopsTicket.project_id == Project.project_id)
                    & (DevsecopsTicket.specialization_id.in_(specialization_ids)),
                )
                .where(Status.is_active == 1)
                .group_by(Status.status_name)
                .order_by(Status.status_name.asc())
            )
        else:
            # Without specialization filter: LEFT JOIN statuses → projects
            # Count all active projects per status
            stmt = (
                select(
                    Status.status_name,
                    func.count(distinct(Project.project_id)).label("count"),
                )
                .select_from(Status)
                .outerjoin(
                    Project,
                    (Project.status_id == Status.status_id) & (Project.is_active == 1),
                )
                .where(Status.is_active == 1)
                .group_by(Status.status_name)
                .order_by(Status.status_name.asc())
            )

        result = await self._session.execute(stmt)
        rows = result.all()

        return [{"status_name": row.status_name, "count": row.count} for row in rows]

    async def get_distinct_clients(self) -> list[str]:
        """Get distinct non-null, non-empty client values from active projects.

        Returns:
            Sorted list of unique client strings.
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

        return list(rows)
