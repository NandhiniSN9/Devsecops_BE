"""Repository for overview dashboard data access operations.

Provides KPI history retrieval for the overview API endpoint.
Fetches current and comparison records to calculate trends.
"""

import uuid
from datetime import datetime, timedelta

from sqlalchemy import String, case, distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.schema.devsecops_ticket import DevsecopsTicket
from src.repositories.schema.kpi_history import KpiHistory
from src.repositories.schema.project import Project
from src.repositories.schema.specialization import Specialization
from src.repositories.schema.status import Status


class OverviewRepository:
    """Data access layer for overview dashboard queries."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_current_records(
        self,
        specialization_ids: list[uuid.UUID] | None,
    ) -> list[KpiHistory]:
        """Get the most recent KPI record per specialization (today or yesterday).

        Tries today first. If no record exists for today, falls back to yesterday.
        Returns one record per active specialization.

        Args:
            specialization_ids: Optional list of specialization UUIDs to filter by.

        Returns:
            List of KpiHistory records (one per matching specialization).
        """
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday_start = today_start - timedelta(days=1)

        # Try to get the latest record per specialization from today or yesterday
        # Using ROW_NUMBER to pick the most recent record per specialization
        row_number = (
            func.row_number()
            .over(
                partition_by=KpiHistory.specialization_id,
                order_by=KpiHistory.created_at.desc(),
            )
            .label("row_number")
        )

        subquery = (
            select(KpiHistory, row_number)
            .join(
                Specialization,
                KpiHistory.specialization_id == Specialization.specialization_id,
            )
            .where(
                KpiHistory.created_at >= yesterday_start,
                KpiHistory.is_active == 1,
                Specialization.is_active == 1,
            )
        )

        if specialization_ids:
            subquery = subquery.where(KpiHistory.specialization_id.in_(specialization_ids))

        subquery = subquery.subquery()

        stmt = select(KpiHistory).from_statement(
            select(subquery).where(subquery.c.row_number == 1)
        )

        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_comparison_records(
        self,
        specialization_ids: list[uuid.UUID] | None,
        period_days: int,
    ) -> list[KpiHistory]:
        """Get the KPI record per specialization from N days ago.

        Tries the exact date first. If no record exists for that date,
        falls back to the closest previous record before that date.

        Args:
            specialization_ids: Optional list of specialization UUIDs to filter by.
            period_days: Number of days to look back (7, 30, or 90).

        Returns:
            List of KpiHistory records (one per matching specialization).
        """
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        target_date = today_start - timedelta(days=period_days)

        # Get the most recent record per specialization that is on or before the target date
        row_number = (
            func.row_number()
            .over(
                partition_by=KpiHistory.specialization_id,
                order_by=KpiHistory.created_at.desc(),
            )
            .label("row_number")
        )

        subquery = (
            select(KpiHistory, row_number)
            .join(
                Specialization,
                KpiHistory.specialization_id == Specialization.specialization_id,
            )
            .where(
                KpiHistory.created_at <= target_date + timedelta(days=1),
                KpiHistory.is_active == 1,
                Specialization.is_active == 1,
            )
        )

        if specialization_ids:
            subquery = subquery.where(KpiHistory.specialization_id.in_(specialization_ids))

        subquery = subquery.subquery()

        stmt = select(KpiHistory).from_statement(
            select(subquery).where(subquery.c.row_number == 1)
        )

        result = await self._session.execute(stmt)
        return list(result.scalars().all())

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
