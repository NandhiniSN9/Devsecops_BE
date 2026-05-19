"""Overview service for KPI aggregation and trend calculation.

Computes live project counts from the database and calculates
trends by comparing current counts with historical snapshots.
"""

from src.models.request.overview_request import PeriodEnum
from src.models.response.overview_response import (
    KpiTileResponse,
    OverviewDataResponse,
    OverviewMetricsResponse,
    StatusBreakdownItemResponse,
    StatusDistributionResponse,
    SyncDetailResponse,
)
from src.repositories.overview_repository import OverviewRepository
from src.settings import PERIOD_DAYS_MAP
from src.utils.exceptions.exceptions import InvalidParameterError
from src.utils.logger import logger


class OverviewService:
    """Service for computing overview dashboard data.

    Calculates KPI metrics by comparing live counts from the projects table
    with historical snapshots from kpi_history to derive trends.
    """

    def __init__(self, overview_repo: OverviewRepository) -> None:
        """Initialize with repository dependency."""
        self._overview_repo = overview_repo

    async def get_overview(self, period: str | None) -> OverviewDataResponse:
        """Compute and return the full overview dashboard data.

        Args:
            period: Period filter value (last_week, last_month, last_3_months) or None.

        Returns:
            OverviewDataResponse containing metrics and status distribution.

        Raises:
            InvalidParameterError: If period is invalid or empty string.
        """
        try:
            # Step 1: Validate period
            validated_period = self._validate_period(period)
            period_days = PERIOD_DAYS_MAP[validated_period]

            # Step 2: Get sync details
            last_synced_dt = await self._overview_repo.get_last_synced()
            last_synced = last_synced_dt.strftime("%d %b %Y, %H:%M") if last_synced_dt else None
            is_sync_in_progress = await self._overview_repo.is_sync_in_progress()

            sync_detail = SyncDetailResponse(
                last_sync_datetime=last_synced,
                is_sync_in_progress=is_sync_in_progress,
            )

            # Step 3: Get live counts from projects table
            current_counts = await self._overview_repo.get_live_counts()

            # Step 4: Get historical counts for trend comparison
            historical_counts = await self._overview_repo.get_historical_counts(period_days)

            # Step 5: Build metrics with trends
            metrics = self._build_metrics(current_counts, historical_counts)

            # Step 6: Build status distribution
            status_distribution = self._build_status_distribution(current_counts)

            return OverviewDataResponse(
                sync_detail=sync_detail,
                metrics=metrics,
                status_distribution=status_distribution,
            )

        except InvalidParameterError:
            raise
        except Exception as exc:
            logger.error("Error computing overview data", error=str(exc))
            raise

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

        if period == "":
            accepted = [e.value for e in PeriodEnum]
            raise InvalidParameterError(f"Invalid value for parameter 'period'. Accepted values: {accepted}")

        valid_values = [e.value for e in PeriodEnum]
        if period not in valid_values:
            raise InvalidParameterError(f"Invalid value for parameter 'period'. Accepted values: {valid_values}")

        return period

    def _build_metrics(self, current: dict, historical: dict | None) -> OverviewMetricsResponse:
        """Build KPI metrics by comparing current vs historical counts.

        Change = current_count - historical_count
        Trend = increase/decrease/flat based on change sign.
        If no historical data exists, trend is None.

        Args:
            current: Current live counts dict.
            historical: Historical counts dict from N days ago, or None.

        Returns:
            OverviewMetricsResponse with all seven KPI tiles.
        """
        try:
            if historical is None:
                # No historical data — show counts with null trends
                return OverviewMetricsResponse(
                    total_projects=KpiTileResponse(count=current["total_projects"], trend=None, change=0),
                    adopted=KpiTileResponse(count=current["adopted"], trend=None, change=0),
                    completed=KpiTileResponse(count=current["completed"], trend=None, change=0),
                    active=KpiTileResponse(count=current["active"], trend=None, change=0),
                    inactive=KpiTileResponse(count=current["inactive"], trend=None, change=0),
                    at_risk=KpiTileResponse(count=current["at_risk"], trend=None, change=0),
                    not_applicable=KpiTileResponse(count=current["not_applicable"], trend=None, change=0),
                )

            return OverviewMetricsResponse(
                total_projects=self._build_tile(current["total_projects"], historical["total_projects"]),
                adopted=self._build_tile(current["adopted"], historical["adopted"]),
                completed=self._build_tile(current["completed"], historical["completed"]),
                active=self._build_tile(current["active"], historical["active"]),
                inactive=self._build_tile(current["inactive"], historical["inactive"]),
                at_risk=self._build_tile(current["at_risk"], historical["at_risk"]),
                not_applicable=self._build_tile(current["not_applicable"], historical["not_applicable"]),
            )

        except Exception as exc:
            logger.error("Error building metrics", error=str(exc))
            raise

    @staticmethod
    def _build_tile(current_count: int, comparison_count: int) -> KpiTileResponse:
        """Build a KPI tile from current and comparison counts.

        Args:
            current_count: The current (latest) count value.
            comparison_count: The count from N days ago.

        Returns:
            KpiTileResponse with count, trend direction, and absolute change.
        """
        change = current_count - comparison_count

        if change > 0:
            trend = "increase"
        elif change < 0:
            trend = "decrease"
        else:
            trend = "flat"

        return KpiTileResponse(count=current_count, trend=trend, change=abs(change))

    def _build_status_distribution(self, counts: dict) -> StatusDistributionResponse:
        """Build status distribution from live counts.

        Args:
            counts: Current live counts dict.

        Returns:
            StatusDistributionResponse with total and breakdown items.
        """
        try:
            total = counts["total_projects"]

            breakdown_data = [
                {"status_name": "Adopted", "count": counts["adopted"]},
                {"status_name": "Active", "count": counts["active"]},
                {"status_name": "At Risk", "count": counts["at_risk"]},
                {"status_name": "Completed", "count": counts["completed"]},
                {"status_name": "Inactive", "count": counts["inactive"]},
                {"status_name": "Not Applicable", "count": counts["not_applicable"]},
            ]

            breakdown: list[StatusBreakdownItemResponse] = []
            for item in breakdown_data:
                if total == 0:
                    percentage = 0.0
                else:
                    percentage = round((item["count"] / total) * 100, 1)

                breakdown.append(
                    StatusBreakdownItemResponse(
                        status=item["status_name"],
                        count=item["count"],
                        percentage=percentage,
                    )
                )

            return StatusDistributionResponse(total=total, breakdown=breakdown)

        except Exception as exc:
            logger.error("Error building status distribution", error=str(exc))
            raise
