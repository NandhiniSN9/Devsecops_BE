"""Repository for KPI history data access operations."""

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.schema.kpi_history import KpiHistory
from src.repositories.schema.specialization import Specialization


class KpiHistoryRepository:
    """Repository for querying KPI history records."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with an async database session."""
        self._session = session

    async def get_latest_by_specializations(
        self,
        specialization_ids: list[uuid.UUID] | None,
        period_days: int,
    ) -> list[KpiHistory]:
        """Get the most recent KPI history record per active specialization within the period.

        Uses ROW_NUMBER() window function partitioned by specialization_id and ordered
        by created_at DESC to select only the latest record per specialization.

        Args:
            specialization_ids: Optional list of specialization UUIDs to filter by.
                When None, returns data for all active specializations.
            period_days: Number of days to look back from current time.

        Returns:
            List of KpiHistory records (one per matching specialization).
        """
        # Calculate the cutoff date for the period filter
        cutoff_date = datetime.now(UTC) - timedelta(days=period_days)

        # Build the window function for selecting the most recent record per specialization
        row_number = (
            func.row_number()
            .over(
                partition_by=KpiHistory.specialization_id,
                order_by=KpiHistory.created_at.desc(),
            )
            .label("row_number")
        )

        # Build the subquery with window function
        subquery = (
            select(KpiHistory, row_number)
            .join(
                Specialization,
                KpiHistory.specialization_id == Specialization.specialization_id,
            )
            .where(
                KpiHistory.created_at >= cutoff_date,
                KpiHistory.is_active == 1,
                Specialization.is_active == 1,
            )
        )

        # Apply specialization filter if provided
        if specialization_ids:
            subquery = subquery.where(KpiHistory.specialization_id.in_(specialization_ids))

        subquery = subquery.subquery()

        # Select only the most recent record per specialization (row_number = 1)
        stmt = select(KpiHistory).from_statement(select(subquery).where(subquery.c.row_number == 1))

        result = await self._session.execute(stmt)
        return list(result.scalars().all())
