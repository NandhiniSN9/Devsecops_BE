"""Overview service for KPI aggregation and trend calculation."""

import uuid

from src.models.overview_models import (
    KpiTile,
    OverviewData,
    OverviewMetrics,
    StatusBreakdownItem,
    StatusDistribution,
    SyncDetail,
)
from src.models.query_params import PeriodEnum
from src.repositories.overview_repository import OverviewRepository
from src.repositories.schema.kpi_history import KpiHistory
from src.settings import (
    MAX_SPECIALIZATION_FILTER_COUNT,
    PERIOD_DAYS_MAP,
)
from src.utils.exceptions import InvalidParameterError


class OverviewService:
    """Service for computing overview dashboard data.

    Calculates KPI metrics by comparing the current record (today/yesterday)
    with the record from N days ago to derive trends and change values.
    """

    def __init__(
        self,
        overview_repo: OverviewRepository,
    ) -> None:
        """Initialize with repository dependency."""
        self._overview_repo = overview_repo

    async def get_overview(self, period: str | None, specialization: str | None) -> OverviewData:
        """Compute and return the full overview dashboard data.

        Args:
            period: Period filter value (last_week, last_month, last_3_months) or None.
            specialization: Comma-separated specialization UUIDs or None.

        Returns:
            OverviewData containing metrics and status distribution.

        Raises:
            InvalidParameterError: If period is invalid or empty string.
        """
        # Step 1: Validate period BEFORE specialization (fail fast)
        validated_period = self._validate_period(period)
        period_days = PERIOD_DAYS_MAP[validated_period]

        # Step 2: Parse specialization filter
        specialization_ids = self._parse_specialization(specialization)

        # Step 3: Get last_synced from settings
        last_synced_dt = await self._overview_repo.get_last_synced(specialization_ids)
        last_synced = last_synced_dt.strftime("%d %b %Y, %H:%M") if last_synced_dt else None

        # Step 4: Check if sync is in progress
        is_sync_in_progress = await self._overview_repo.is_sync_in_progress()

        # Step 5: Build sync_detail object
        sync_detail = SyncDetail(
            last_sync_datetime=last_synced,
            is_sync_in_progress=is_sync_in_progress,
        )

        # Step 6: Get current and comparison KPI records, compute metrics
        current_records = await self._overview_repo.get_current_records(specialization_ids)
        metrics = await self._compute_metrics(current_records, specialization_ids, period_days)

        # Step 7: Compute status distribution from KPI counts
        total_projects = metrics.total_projects.count
        status_distribution = await self._compute_status_distribution(current_records, total_projects)

        return OverviewData(
            sync_detail=sync_detail,
            metrics=metrics,
            status_distribution=status_distribution,
        )

    def _validate_period(self, period: str | None) -> str:
        """Validate and normalize the period parameter.

        Args:
            period: Raw period value from query parameter.

        Returns:
            Validated period string.

        Raises:
            InvalidParameterError: If period is empty string or not a valid enum value.
        """
        if period is None:
            return PeriodEnum.LAST_WEEK.value

        # Empty string is invalid
        if period == "":
            accepted = [e.value for e in PeriodEnum]
            raise InvalidParameterError(f"Invalid value for parameter 'period'. Accepted values: {accepted}")

        # Check against valid enum values
        valid_values = [e.value for e in PeriodEnum]
        if period not in valid_values:
            raise InvalidParameterError(f"Invalid value for parameter 'period'. Accepted values: {valid_values}")

        return period

    def _parse_specialization(self, specialization: str | None) -> list[uuid.UUID] | None:
        """Parse the specialization CSV parameter into a list of UUIDs.

        Args:
            specialization: Comma-separated specialization IDs or None.

        Returns:
            List of valid UUIDs, or None if no filter should be applied.
        """
        if specialization is None or specialization.strip() == "":
            return None

        # Split by comma, trim whitespace, limit to MAX_SPECIALIZATION_FILTER_COUNT
        raw_ids = specialization.split(",")
        trimmed_ids = [id_str.strip() for id_str in raw_ids]
        limited_ids = trimmed_ids[:MAX_SPECIALIZATION_FILTER_COUNT]

        # Parse as UUID, skip non-UUID values
        valid_uuids: list[uuid.UUID] = []
        for id_str in limited_ids:
            try:
                valid_uuids.append(uuid.UUID(id_str))
            except (ValueError, AttributeError):
                continue

        # All invalid IDs → treated as no filter (return all)
        if not valid_uuids:
            return None

        return valid_uuids

    async def _compute_metrics(
        self, current_records: list, specialization_ids: list[uuid.UUID] | None, period_days: int
    ) -> OverviewMetrics:
        """Compute KPI metrics by comparing current vs comparison records.

        Current record: today's record, or yesterday's if today doesn't exist.
        Comparison record: record from exactly N days ago, or closest previous.

        Change = current.count - comparison.count
        Trend = increase/decrease/flat based on change sign.

        Args:
            current_records: Already-fetched current KPI records.
            specialization_ids: Optional list of specialization UUIDs to filter by.
            period_days: Number of days to look back for comparison.

        Returns:
            OverviewMetrics with all six KPI tiles.
        """
        # If no current records → all zeros
        if not current_records:
            null_tile = KpiTile(count=0, trend=None, change=0)
            return OverviewMetrics(
                total_projects=null_tile,
                completed=null_tile,
                active=null_tile,
                inactive=null_tile,
                at_risk=null_tile,
                not_applicable=null_tile,
            )

        # Fetch comparison records (N days ago or closest previous) per specialization
        comparison_records = await self._overview_repo.get_comparison_records(specialization_ids, period_days)

        # Build comparison lookup by specialization_id
        comparison_map: dict[uuid.UUID, KpiHistory] = {}
        for record in comparison_records:
            if record.specialization_id:
                comparison_map[record.specialization_id] = record

        # Sum current counts across all specializations
        total_projects_current = sum((r.projects_count or 0) for r in current_records)
        completed_current = sum((r.completed_count or 0) for r in current_records)
        active_current = sum((r.active_count or 0) for r in current_records)
        inactive_current = sum((r.inactive_count or 0) for r in current_records)
        at_risk_current = sum((r.at_risk_count or 0) for r in current_records)
        not_applicable_current = sum((r.not_applicable_count or 0) for r in current_records)

        # Sum comparison counts (matching specializations)
        total_projects_comparison = 0
        completed_comparison = 0
        active_comparison = 0
        inactive_comparison = 0
        at_risk_comparison = 0
        not_applicable_comparison = 0

        for record in current_records:
            comp = comparison_map.get(record.specialization_id) if record.specialization_id else None
            if comp:
                total_projects_comparison += comp.projects_count or 0
                completed_comparison += comp.completed_count or 0
                active_comparison += comp.active_count or 0
                inactive_comparison += comp.inactive_count or 0
                at_risk_comparison += comp.at_risk_count or 0
                not_applicable_comparison += comp.not_applicable_count or 0

        # Calculate change and derive trends
        return OverviewMetrics(
            total_projects=self._build_tile(total_projects_current, total_projects_comparison),
            completed=self._build_tile(completed_current, completed_comparison),
            active=self._build_tile(active_current, active_comparison),
            inactive=self._build_tile(inactive_current, inactive_comparison),
            at_risk=self._build_tile(at_risk_current, at_risk_comparison),
            not_applicable=self._build_tile(not_applicable_current, not_applicable_comparison),
        )

    @staticmethod
    def _build_tile(current_count: int, comparison_count: int) -> KpiTile:
        """Build a KPI tile from current and comparison counts.

        Args:
            current_count: The current (latest) count value.
            comparison_count: The count from N days ago.

        Returns:
            KpiTile with count, trend direction, and absolute change.
        """
        change = current_count - comparison_count

        if change > 0:
            trend = "increase"
        elif change < 0:
            trend = "decrease"
        else:
            trend = "flat"

        return KpiTile(count=current_count, trend=trend, change=abs(change))

    async def _compute_status_distribution(
        self, current_records: list, total_projects: int
    ) -> StatusDistribution:
        """Compute status distribution from KPI history counts.

        total = projects_count (sum across specializations)
        breakdown = completed + active + inactive + at_risk + not_applicable
        percentage = (count / total) * 100

        Args:
            current_records: Current KPI records per specialization.
            total_projects: Total projects count (sum of projects_count).

        Returns:
            StatusDistribution with total and breakdown items.
        """
        completed = sum((r.completed_count or 0) for r in current_records)
        active = sum((r.active_count or 0) for r in current_records)
        inactive = sum((r.inactive_count or 0) for r in current_records)
        at_risk = sum((r.at_risk_count or 0) for r in current_records)
        not_applicable = sum((r.not_applicable_count or 0) for r in current_records)

        breakdown_data = [
            {"status_name": "Active", "count": active},
            {"status_name": "At Risk", "count": at_risk},
            {"status_name": "Completed", "count": completed},
            {"status_name": "Inactive", "count": inactive},
            {"status_name": "Not Applicable", "count": not_applicable},
        ]

        breakdown: list[StatusBreakdownItem] = []
        for item in breakdown_data:
            if total_projects == 0:
                percentage = 0.0
            else:
                percentage = round((item["count"] / total_projects) * 100, 1)

            breakdown.append(
                StatusBreakdownItem(
                    status=item["status_name"],
                    count=item["count"],
                    percentage=percentage,
                )
            )

        return StatusDistribution(total=total_projects, breakdown=breakdown)
