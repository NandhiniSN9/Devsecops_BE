"""Repository for overview dashboard data access operations.

Provides KPI history retrieval for the overview API endpoint.
Fetches current and comparison records to calculate trends.
"""

import uuid
from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.schema.kpi_history import KpiHistory
from src.repositories.schema.setting import Setting
from src.repositories.schema.specialization import Specialization


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

    async def get_last_synced(self, specialization_ids: list[uuid.UUID] | None) -> datetime | None:
        """Get the most recent last_synced timestamp from the settings table.

        When specialization_ids is provided, filters settings by those specializations.
        Returns the maximum (most recent) last_synced value.

        Args:
            specialization_ids: Optional list of specialization UUIDs to filter by.

        Returns:
            The most recent last_synced datetime, or None if no records found.
        """
        stmt = select(func.max(Setting.last_synced)).where(Setting.is_active == 1)

        if specialization_ids:
            stmt = stmt.where(Setting.specialization_id.in_(specialization_ids))

        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
