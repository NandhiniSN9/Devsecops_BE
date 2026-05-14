"""Overview service for KPI aggregation, trend derivation, and attention banner logic."""

import uuid

from src.models.overview_models import (
    AttentionBanner,
    KpiTile,
    OverviewData,
    OverviewMetrics,
    StatusBreakdownItem,
    StatusDistribution,
)
from src.models.query_params import PeriodEnum
from src.repositories.kpi_history_repository import KpiHistoryRepository
from src.repositories.project_repository import ProjectRepository
from src.repositories.specialization_repository import SpecializationRepository
from src.settings import (
    MAX_SPECIALIZATION_FILTER_COUNT,
    PERIOD_DAYS_MAP,
    SEVERITY_CRITICAL_THRESHOLD,
)
from src.utils.exceptions import InvalidParameterError


class OverviewService:
    """Service for computing overview dashboard data."""

    def __init__(
        self,
        kpi_repo: KpiHistoryRepository,
        project_repo: ProjectRepository,
        specialization_repo: SpecializationRepository,
    ) -> None:
        """Initialize with repository dependencies."""
        self._kpi_repo = kpi_repo
        self._project_repo = project_repo
        self._specialization_repo = specialization_repo

    async def get_overview(self, period: str | None, specialization: str | None) -> OverviewData:
        """Compute and return the full overview dashboard data.

        Args:
            period: Period filter value (last_week, last_month, last_3_months) or None.
            specialization: Comma-separated specialization UUIDs or None.

        Returns:
            OverviewData containing metrics, status distribution, and attention banner.

        Raises:
            InvalidParameterError: If period is invalid or empty string.
        """
        # Step 1: Validate period BEFORE specialization (fail fast)
        validated_period = self._validate_period(period)
        period_days = PERIOD_DAYS_MAP[validated_period]

        # Step 2: Parse specialization filter
        specialization_ids = self._parse_specialization(specialization)

        # Step 3: Get KPI data and compute metrics
        metrics = await self._compute_metrics(specialization_ids, period_days)

        # Step 4: Compute status distribution
        status_distribution = await self._compute_status_distribution(specialization_ids)

        # Step 5: Compute attention banner from at_risk count in metrics
        attention_banner = self._compute_attention_banner(metrics.at_risk.count)

        return OverviewData(
            metrics=metrics,
            status_distribution=status_distribution,
            attention_banner=attention_banner,
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

    async def _compute_metrics(self, specialization_ids: list[uuid.UUID] | None, period_days: int) -> OverviewMetrics:
        """Compute KPI metrics by aggregating latest records per specialization.

        Args:
            specialization_ids: Optional list of specialization UUIDs to filter by.
            period_days: Number of days to look back.

        Returns:
            OverviewMetrics with all six KPI tiles.
        """
        records = await self._kpi_repo.get_latest_by_specializations(specialization_ids, period_days)

        # If no records found → all counts = 0, all trends = null, all changes = 0
        if not records:
            null_tile = KpiTile(count=0, trend=None, change=0)
            return OverviewMetrics(
                total_projects=null_tile,
                completed=null_tile,
                active=null_tile,
                inactive=null_tile,
                at_risk=null_tile,
                not_applicable=null_tile,
            )

        # Sum counts across all records
        total_projects_count = sum((r.projects_count or 0) for r in records)
        total_projects_increase = sum((r.projects_increase_count or 0) for r in records)
        total_projects_decrease = sum((r.projects_decrease_count or 0) for r in records)

        completed_count = sum((r.completed_count or 0) for r in records)
        completed_increase = sum((r.completed_increase_count or 0) for r in records)
        completed_decrease = sum((r.completed_decrease_count or 0) for r in records)

        active_count = sum((r.active_count or 0) for r in records)
        active_increase = sum((r.active_increase_count or 0) for r in records)
        active_decrease = sum((r.active_decrease_count or 0) for r in records)

        inactive_count = sum((r.inactive_count or 0) for r in records)
        inactive_increase = sum((r.inactive_increase_count or 0) for r in records)
        inactive_decrease = sum((r.inactive_decrease_count or 0) for r in records)

        at_risk_count = sum((r.at_risk_count or 0) for r in records)
        at_risk_increase = sum((r.at_risk_increase_count or 0) for r in records)
        at_risk_decrease = sum((r.at_risk_decrease_count or 0) for r in records)

        not_applicable_count = sum((r.not_applicable_count or 0) for r in records)
        not_applicable_increase = sum((r.not_applicable_increase_count or 0) for r in records)
        not_applicable_decrease = sum((r.not_applicable_decrease_count or 0) for r in records)

        # Derive trends
        tp_trend, tp_change = self._derive_trend(total_projects_increase, total_projects_decrease)
        c_trend, c_change = self._derive_trend(completed_increase, completed_decrease)
        a_trend, a_change = self._derive_trend(active_increase, active_decrease)
        i_trend, i_change = self._derive_trend(inactive_increase, inactive_decrease)
        ar_trend, ar_change = self._derive_trend(at_risk_increase, at_risk_decrease)
        na_trend, na_change = self._derive_trend(not_applicable_increase, not_applicable_decrease)

        return OverviewMetrics(
            total_projects=KpiTile(count=total_projects_count, trend=tp_trend, change=tp_change),
            completed=KpiTile(count=completed_count, trend=c_trend, change=c_change),
            active=KpiTile(count=active_count, trend=a_trend, change=a_change),
            inactive=KpiTile(count=inactive_count, trend=i_trend, change=i_change),
            at_risk=KpiTile(count=at_risk_count, trend=ar_trend, change=ar_change),
            not_applicable=KpiTile(count=not_applicable_count, trend=na_trend, change=na_change),
        )

    async def _compute_status_distribution(self, specialization_ids: list[uuid.UUID] | None) -> StatusDistribution:
        """Compute project status distribution with percentages.

        Args:
            specialization_ids: Optional list of specialization UUIDs to filter by.

        Returns:
            StatusDistribution with total count and breakdown items.
        """
        distribution_data = await self._project_repo.get_status_distribution(specialization_ids)

        # Calculate total
        total = sum(item["count"] for item in distribution_data)

        # Build breakdown items with percentage calculation
        breakdown: list[StatusBreakdownItem] = []
        for item in distribution_data:
            if total == 0:
                percentage = 0.0
            else:
                percentage = round((item["count"] / total) * 100, 1)

            breakdown.append(
                StatusBreakdownItem(
                    status=item["status_name"],
                    count=item["count"],
                    percentage=percentage,
                )
            )

        return StatusDistribution(total=total, breakdown=breakdown)

    def _compute_attention_banner(self, at_risk_count: int) -> AttentionBanner:
        """Compute the attention banner based on at-risk project count.

        Args:
            at_risk_count: Number of at-risk projects.

        Returns:
            AttentionBanner with severity and message.
        """
        if at_risk_count >= SEVERITY_CRITICAL_THRESHOLD:
            severity = "critical"
            message = f"{at_risk_count} projects are at risk and require immediate attention."
        elif at_risk_count >= 1:
            severity = "warning"
            plural_s = "s" if at_risk_count > 1 else ""
            verb_s = "s" if at_risk_count == 1 else ""
            message = f"{at_risk_count} project{plural_s} at risk and require{verb_s} attention."
        else:
            severity = "info"
            message = "No projects are currently at risk."

        return AttentionBanner(
            message=message,
            at_risk_count=at_risk_count,
            severity=severity,
        )

    @staticmethod
    def _derive_trend(increase_count: int, decrease_count: int) -> tuple[str | None, int]:
        """Derive trend direction and change value from increase/decrease counts.

        Priority: increase > decrease > flat.
        When both increase and decrease are > 0, "increase" wins.

        Args:
            increase_count: Summed increase count for the metric.
            decrease_count: Summed decrease count for the metric.

        Returns:
            Tuple of (trend_direction, change_value).
        """
        if increase_count > 0:
            return ("increase", increase_count)
        elif decrease_count > 0:
            return ("decrease", decrease_count)
        else:
            return ("flat", 0)
