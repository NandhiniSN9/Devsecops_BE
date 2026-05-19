"""Unit tests for OverviewService.

Tests cover the public get_overview() method and internal helpers:
_build_tile(), _validate_period(), _compute_status_distribution().

Validates: Requirements 1.2, 1.4, 1.10, 2.1, 2.2, 2.3, 2.4, 3.3, 3.4, 4.2, 4.3, 4.4
"""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.models.response.overview_response import (
    OverviewDataResponse,
    OverviewMetricsResponse,
    StatusDistributionResponse,
)
from src.repositories.overview_repository import OverviewRepository
from src.services.overview_service import OverviewService
from src.utils.exceptions import InvalidParameterError


@pytest.fixture
def mock_overview_repo():
    """Create a mock OverviewRepository."""
    return AsyncMock(spec=OverviewRepository)


@pytest.fixture
def service(mock_overview_repo):
    """Create an OverviewService with mocked repository."""
    return OverviewService(
        overview_repo=mock_overview_repo,
    )


def _make_kpi_record(**kwargs):
    """Helper to create a mock KPI history record with sensible defaults."""
    record = MagicMock()
    record.specialization_id = kwargs.get("specialization_id", uuid.uuid4())
    record.projects_count = kwargs.get("projects_count", 10)
    record.completed_count = kwargs.get("completed_count", 5)
    record.active_count = kwargs.get("active_count", 3)
    record.inactive_count = kwargs.get("inactive_count", 1)
    record.at_risk_count = kwargs.get("at_risk_count", 1)
    record.not_applicable_count = kwargs.get("not_applicable_count", 0)
    return record


class TestValidatePeriod:
    """Tests for OverviewService._validate_period."""

    def test_none_defaults_to_last_week(self, service):
        """When period is None, defaults to 'last_week'.

        Validates: Requirements 1.2
        """
        result = service._validate_period(None)
        assert result == "last_week"

    def test_valid_last_week(self, service):
        """Accepts 'last_week' as a valid period value."""
        result = service._validate_period("last_week")
        assert result == "last_week"

    def test_valid_last_month(self, service):
        """Accepts 'last_month' as a valid period value."""
        result = service._validate_period("last_month")
        assert result == "last_month"

    def test_valid_last_3_months(self, service):
        """Accepts 'last_3_months' as a valid period value."""
        result = service._validate_period("last_3_months")
        assert result == "last_3_months"

    def test_invalid_period_raises_error(self, service):
        """Invalid period value raises InvalidParameterError.

        Validates: Requirements 1.4
        """
        with pytest.raises(InvalidParameterError) as exc_info:
            service._validate_period("last_year")
        assert "period" in exc_info.value.message
        assert "last_week" in exc_info.value.message

    def test_empty_string_raises_error(self, service):
        """Empty string period raises InvalidParameterError.

        Validates: Requirements 1.4
        """
        with pytest.raises(InvalidParameterError) as exc_info:
            service._validate_period("")
        assert "period" in exc_info.value.message

    def test_case_sensitive_validation(self, service):
        """Period validation is case-sensitive; 'Last_Week' is invalid.

        Validates: Requirements 1.4
        """
        with pytest.raises(InvalidParameterError):
            service._validate_period("Last_Week")


class TestBuildTile:
    """Tests for OverviewService._build_tile static method."""

    def test_increase(self):
        """When current > comparison, trend is 'increase'.

        Validates: Requirements 2.1
        """
        tile = OverviewService._build_tile(5, 0)
        assert tile.trend == "increase"
        assert tile.change == 5
        assert tile.count == 5

    def test_decrease(self):
        """When current < comparison, trend is 'decrease'.

        Validates: Requirements 2.2
        """
        tile = OverviewService._build_tile(2, 5)
        assert tile.trend == "decrease"
        assert tile.change == 3
        assert tile.count == 2

    def test_flat(self):
        """When current == comparison, trend is 'flat'.

        Validates: Requirements 2.3
        """
        tile = OverviewService._build_tile(5, 5)
        assert tile.trend == "flat"
        assert tile.change == 0
        assert tile.count == 5

    def test_both_zero_is_flat(self):
        """When both are 0, trend is 'flat' with change 0.

        Validates: Requirements 2.3
        """
        tile = OverviewService._build_tile(0, 0)
        assert tile.trend == "flat"
        assert tile.change == 0

    def test_large_increase_value(self):
        """Large increase value is returned correctly."""
        tile = OverviewService._build_tile(1000, 0)
        assert tile.trend == "increase"
        assert tile.change == 1000

    def test_large_decrease_value(self):
        """Large decrease value is returned correctly."""
        tile = OverviewService._build_tile(1, 1000)
        assert tile.trend == "decrease"
        assert tile.change == 999


class TestGetOverview:
    """Tests for OverviewService.get_overview (integration with mocked repos)."""

    async def test_default_period_returns_last_week_data(
        self, service, mock_overview_repo
    ):
        """Valid request with default period (None) uses last_week (7 days).

        Validates: Requirements 1.2
        """
        mock_overview_repo.get_last_synced.return_value = None
        mock_overview_repo.is_sync_in_progress.return_value = False
        mock_overview_repo.get_current_records.return_value = []
        mock_overview_repo.get_comparison_records.return_value = []

        await service.get_overview(period=None)

        mock_overview_repo.get_current_records.assert_called_once_with(None)

    async def test_explicit_last_month_uses_30_days(
        self, service, mock_overview_repo
    ):
        """Explicit 'last_month' period filters by 30 days."""
        mock_overview_repo.get_last_synced.return_value = None
        mock_overview_repo.is_sync_in_progress.return_value = False
        mock_overview_repo.get_current_records.return_value = []
        mock_overview_repo.get_comparison_records.return_value = []

        await service.get_overview(period="last_month")

        mock_overview_repo.get_current_records.assert_called_once_with(None)

    async def test_explicit_last_3_months_uses_90_days(
        self, service, mock_overview_repo
    ):
        """Explicit 'last_3_months' period filters by 90 days."""
        mock_overview_repo.get_last_synced.return_value = None
        mock_overview_repo.is_sync_in_progress.return_value = False
        mock_overview_repo.get_current_records.return_value = []
        mock_overview_repo.get_comparison_records.return_value = []

        await service.get_overview(period="last_3_months")

        mock_overview_repo.get_current_records.assert_called_once_with(None)

    async def test_invalid_period_raises_error(self, service):
        """Invalid period raises InvalidParameterError before querying repos.

        Validates: Requirements 1.4
        """
        with pytest.raises(InvalidParameterError):
            await service.get_overview(period="invalid")

    async def test_empty_period_raises_error(self, service):
        """Empty period string raises InvalidParameterError.

        Validates: Requirements 1.4
        """
        with pytest.raises(InvalidParameterError):
            await service.get_overview(period="")

    async def test_no_kpi_records_returns_zeros_with_null_trends(
        self, service, mock_overview_repo
    ):
        """No KPI history records returns all zeros with null trends.

        Validates: Requirements 1.10
        """
        mock_overview_repo.get_last_synced.return_value = None
        mock_overview_repo.is_sync_in_progress.return_value = False
        mock_overview_repo.get_current_records.return_value = []
        mock_overview_repo.get_comparison_records.return_value = []

        result = await service.get_overview(period=None)

        assert isinstance(result, OverviewDataResponse)
        metrics = result.metrics
        for tile in [
            metrics.total_projects,
            metrics.completed,
            metrics.active,
            metrics.inactive,
            metrics.at_risk,
            metrics.not_applicable,
        ]:
            assert tile.count == 0
            assert tile.trend is None
            assert tile.change == 0

    async def test_kpi_records_aggregated_correctly(
        self, service, mock_overview_repo
    ):
        """KPI records are summed across specializations correctly."""
        spec_id_1 = uuid.uuid4()
        spec_id_2 = uuid.uuid4()
        record1 = _make_kpi_record(
            specialization_id=spec_id_1,
            projects_count=10,
            completed_count=5,
            active_count=3,
            inactive_count=1,
            at_risk_count=3,
            not_applicable_count=0,
        )
        record2 = _make_kpi_record(
            specialization_id=spec_id_2,
            projects_count=5,
            completed_count=2,
            active_count=2,
            inactive_count=0,
            at_risk_count=2,
            not_applicable_count=0,
        )
        mock_overview_repo.get_last_synced.return_value = None
        mock_overview_repo.is_sync_in_progress.return_value = False
        mock_overview_repo.get_current_records.return_value = [record1, record2]
        mock_overview_repo.get_comparison_records.return_value = []

        result = await service.get_overview(period=None)

        assert result.metrics.total_projects.count == 15
        assert result.metrics.at_risk.count == 5

    async def test_returns_overview_data_type(
        self, service, mock_overview_repo
    ):
        """get_overview returns an OverviewDataResponse instance."""
        mock_overview_repo.get_last_synced.return_value = None
        mock_overview_repo.is_sync_in_progress.return_value = False
        mock_overview_repo.get_current_records.return_value = []
        mock_overview_repo.get_comparison_records.return_value = []

        result = await service.get_overview(period=None)

        assert isinstance(result, OverviewDataResponse)
        assert isinstance(result.metrics, OverviewMetricsResponse)
        assert isinstance(result.status_distribution, StatusDistributionResponse)


class TestStatusDistributionComputation:
    """Tests for status distribution percentage calculation."""

    async def test_percentage_calculation(self, service, mock_overview_repo):
        """Percentages are calculated correctly as (count/total)*100 rounded to 1 decimal.

        Validates: Requirements 3.3
        """
        spec_id = uuid.uuid4()
        record = _make_kpi_record(
            specialization_id=spec_id,
            projects_count=10,
            completed_count=3,
            active_count=7,
            inactive_count=0,
            at_risk_count=0,
            not_applicable_count=0,
        )
        mock_overview_repo.get_last_synced.return_value = None
        mock_overview_repo.is_sync_in_progress.return_value = False
        mock_overview_repo.get_current_records.return_value = [record]
        mock_overview_repo.get_comparison_records.return_value = []

        result = await service.get_overview(period=None)

        breakdown = result.status_distribution.breakdown
        assert result.status_distribution.total == 10
        # Find Active and Completed in breakdown
        active_item = next(b for b in breakdown if b.status == "Active")
        completed_item = next(b for b in breakdown if b.status == "Completed")
        assert active_item.percentage == 70.0
        assert completed_item.percentage == 30.0

    async def test_zero_total_returns_zero_percentages(self, service, mock_overview_repo):
        """When total is zero, all percentages are 0.0 (no division by zero).

        Validates: Requirements 3.4
        """
        mock_overview_repo.get_last_synced.return_value = None
        mock_overview_repo.is_sync_in_progress.return_value = False
        mock_overview_repo.get_current_records.return_value = []
        mock_overview_repo.get_comparison_records.return_value = []

        result = await service.get_overview(period=None)

        assert result.status_distribution.total == 0

    async def test_single_status_gets_100_percent(self, service, mock_overview_repo):
        """Single status with all projects gets 100.0%."""
        spec_id = uuid.uuid4()
        record = _make_kpi_record(
            specialization_id=spec_id,
            projects_count=15,
            completed_count=0,
            active_count=15,
            inactive_count=0,
            at_risk_count=0,
            not_applicable_count=0,
        )
        mock_overview_repo.get_last_synced.return_value = None
        mock_overview_repo.is_sync_in_progress.return_value = False
        mock_overview_repo.get_current_records.return_value = [record]
        mock_overview_repo.get_comparison_records.return_value = []

        result = await service.get_overview(period=None)

        assert result.status_distribution.total == 15
        active_item = next(b for b in result.status_distribution.breakdown if b.status == "Active")
        assert active_item.percentage == 100.0

    async def test_percentage_rounding_to_one_decimal(self, service, mock_overview_repo):
        """Percentages are rounded to one decimal place.

        Validates: Requirements 3.3
        """
        spec_id = uuid.uuid4()
        record = _make_kpi_record(
            specialization_id=spec_id,
            projects_count=6,
            completed_count=2,
            active_count=1,
            inactive_count=3,
            at_risk_count=0,
            not_applicable_count=0,
        )
        mock_overview_repo.get_last_synced.return_value = None
        mock_overview_repo.is_sync_in_progress.return_value = False
        mock_overview_repo.get_current_records.return_value = [record]
        mock_overview_repo.get_comparison_records.return_value = []

        result = await service.get_overview(period=None)

        breakdown = result.status_distribution.breakdown
        active_item = next(b for b in breakdown if b.status == "Active")
        completed_item = next(b for b in breakdown if b.status == "Completed")
        inactive_item = next(b for b in breakdown if b.status == "Inactive")
        # 1/6 = 16.7, 2/6 = 33.3, 3/6 = 50.0
        assert active_item.percentage == pytest.approx(16.7, abs=0.01)
        assert completed_item.percentage == pytest.approx(33.3, abs=0.01)
        assert inactive_item.percentage == pytest.approx(50.0, abs=0.01)

    async def test_empty_records_returns_zero_total(self, service, mock_overview_repo):
        """Empty KPI records returns total 0."""
        mock_overview_repo.get_last_synced.return_value = None
        mock_overview_repo.is_sync_in_progress.return_value = False
        mock_overview_repo.get_current_records.return_value = []
        mock_overview_repo.get_comparison_records.return_value = []

        result = await service.get_overview(period=None)

        assert result.status_distribution.total == 0
