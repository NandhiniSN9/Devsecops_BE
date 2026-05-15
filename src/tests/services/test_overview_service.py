"""Unit tests for OverviewService.

Tests cover the public get_overview() method and internal helpers:
_derive_trend(), _validate_period(), _parse_specialization(), _compute_attention_banner().

Validates: Requirements 1.2, 1.4, 1.7, 1.10, 2.1, 2.2, 2.3, 2.4, 3.3, 3.4, 4.2, 4.3, 4.4
"""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.models.overview_models import (
    OverviewData,
    OverviewMetrics,
    StatusDistribution,
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
    record.projects_count = kwargs.get("projects_count", 10)
    record.projects_increase_count = kwargs.get("projects_increase_count", 2)
    record.projects_decrease_count = kwargs.get("projects_decrease_count", 0)
    record.completed_count = kwargs.get("completed_count", 5)
    record.completed_increase_count = kwargs.get("completed_increase_count", 1)
    record.completed_decrease_count = kwargs.get("completed_decrease_count", 0)
    record.active_count = kwargs.get("active_count", 3)
    record.active_increase_count = kwargs.get("active_increase_count", 0)
    record.active_decrease_count = kwargs.get("active_decrease_count", 1)
    record.inactive_count = kwargs.get("inactive_count", 1)
    record.inactive_increase_count = kwargs.get("inactive_increase_count", 0)
    record.inactive_decrease_count = kwargs.get("inactive_decrease_count", 0)
    record.at_risk_count = kwargs.get("at_risk_count", 1)
    record.at_risk_increase_count = kwargs.get("at_risk_increase_count", 1)
    record.at_risk_decrease_count = kwargs.get("at_risk_decrease_count", 0)
    record.not_applicable_count = kwargs.get("not_applicable_count", 0)
    record.not_applicable_increase_count = kwargs.get("not_applicable_increase_count", 0)
    record.not_applicable_decrease_count = kwargs.get("not_applicable_decrease_count", 0)
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


class TestParseSpecialization:
    """Tests for OverviewService._parse_specialization."""

    def test_none_returns_none(self, service):
        """None specialization returns None (no filter)."""
        result = service._parse_specialization(None)
        assert result is None

    def test_empty_string_returns_none(self, service):
        """Empty string specialization returns None (no filter)."""
        result = service._parse_specialization("")
        assert result is None

    def test_whitespace_only_returns_none(self, service):
        """Whitespace-only specialization returns None (no filter)."""
        result = service._parse_specialization("   ")
        assert result is None

    def test_valid_single_uuid(self, service):
        """Single valid UUID is parsed correctly."""
        test_uuid = str(uuid.uuid4())
        result = service._parse_specialization(test_uuid)
        assert result is not None
        assert len(result) == 1
        assert result[0] == uuid.UUID(test_uuid)

    def test_valid_multiple_uuids(self, service):
        """Multiple valid UUIDs are parsed correctly."""
        uuid1 = str(uuid.uuid4())
        uuid2 = str(uuid.uuid4())
        result = service._parse_specialization(f"{uuid1},{uuid2}")
        assert result is not None
        assert len(result) == 2

    def test_all_invalid_uuids_returns_none(self, service):
        """All invalid UUIDs returns None (treated as no filter).

        Validates: Requirements 1.7
        """
        result = service._parse_specialization("not-a-uuid,also-invalid")
        assert result is None

    def test_mix_valid_and_invalid_uuids(self, service):
        """Mix of valid and invalid UUIDs keeps only valid ones."""
        valid_uuid = str(uuid.uuid4())
        result = service._parse_specialization(f"{valid_uuid},not-a-uuid")
        assert result is not None
        assert len(result) == 1
        assert result[0] == uuid.UUID(valid_uuid)

    def test_trims_whitespace_around_uuids(self, service):
        """Whitespace around UUIDs is trimmed."""
        test_uuid = str(uuid.uuid4())
        result = service._parse_specialization(f"  {test_uuid}  ")
        assert result is not None
        assert len(result) == 1

    def test_limits_to_50_ids(self, service):
        """Specialization IDs are limited to MAX_SPECIALIZATION_FILTER_COUNT (50)."""
        uuids = [str(uuid.uuid4()) for _ in range(55)]
        csv = ",".join(uuids)
        result = service._parse_specialization(csv)
        assert result is not None
        assert len(result) == 50


class TestDeriveTrend:
    """Tests for OverviewService._derive_trend static method."""

    def test_increase_only(self):
        """When increase > 0 and decrease == 0, trend is 'increase'.

        Validates: Requirements 2.1
        """
        trend, change = OverviewService._derive_trend(5, 0)
        assert trend == "increase"
        assert change == 5

    def test_decrease_only(self):
        """When decrease > 0 and increase == 0, trend is 'decrease'.

        Validates: Requirements 2.2
        """
        trend, change = OverviewService._derive_trend(0, 3)
        assert trend == "decrease"
        assert change == 3

    def test_both_zero_is_flat(self):
        """When both increase and decrease are 0, trend is 'flat'.

        Validates: Requirements 2.3
        """
        trend, change = OverviewService._derive_trend(0, 0)
        assert trend == "flat"
        assert change == 0

    def test_both_positive_increase_wins(self):
        """When both increase and decrease > 0, 'increase' takes priority.

        Validates: Requirements 2.4
        """
        trend, change = OverviewService._derive_trend(3, 2)
        assert trend == "increase"
        assert change == 3

    def test_large_increase_value(self):
        """Large increase value is returned correctly."""
        trend, change = OverviewService._derive_trend(1000, 0)
        assert trend == "increase"
        assert change == 1000

    def test_large_decrease_value(self):
        """Large decrease value is returned correctly."""
        trend, change = OverviewService._derive_trend(0, 999)
        assert trend == "decrease"
        assert change == 999


class TestGetOverview:
    """Tests for OverviewService.get_overview (integration with mocked repos)."""

    async def test_default_period_returns_last_week_data(
        self, service, mock_overview_repo
    ):
        """Valid request with default period (None) uses last_week (7 days).

        Validates: Requirements 1.2
        """
        mock_overview_repo.get_latest_by_specializations.return_value = []
        mock_overview_repo.get_status_distribution.return_value = []

        await service.get_overview(period=None, specialization=None)

        mock_overview_repo.get_latest_by_specializations.assert_called_once_with(None, 7)

    async def test_explicit_last_month_uses_30_days(
        self, service, mock_overview_repo
    ):
        """Explicit 'last_month' period filters by 30 days."""
        mock_overview_repo.get_latest_by_specializations.return_value = []
        mock_overview_repo.get_status_distribution.return_value = []

        await service.get_overview(period="last_month", specialization=None)

        mock_overview_repo.get_latest_by_specializations.assert_called_once_with(None, 30)

    async def test_explicit_last_3_months_uses_90_days(
        self, service, mock_overview_repo
    ):
        """Explicit 'last_3_months' period filters by 90 days."""
        mock_overview_repo.get_latest_by_specializations.return_value = []
        mock_overview_repo.get_status_distribution.return_value = []

        await service.get_overview(period="last_3_months", specialization=None)

        mock_overview_repo.get_latest_by_specializations.assert_called_once_with(None, 90)

    async def test_valid_specialization_filter_passes_uuids(
        self, service, mock_overview_repo
    ):
        """Valid specialization filter passes parsed UUIDs to repositories."""
        spec_id = uuid.uuid4()
        mock_overview_repo.get_latest_by_specializations.return_value = []
        mock_overview_repo.get_status_distribution.return_value = []

        await service.get_overview(period=None, specialization=str(spec_id))

        call_args = mock_overview_repo.get_latest_by_specializations.call_args
        assert call_args[0][0] == [spec_id]
        assert call_args[0][1] == 7

    async def test_invalid_period_raises_error(self, service):
        """Invalid period raises InvalidParameterError before querying repos.

        Validates: Requirements 1.4
        """
        with pytest.raises(InvalidParameterError):
            await service.get_overview(period="invalid", specialization=None)

    async def test_empty_period_raises_error(self, service):
        """Empty period string raises InvalidParameterError.

        Validates: Requirements 1.4
        """
        with pytest.raises(InvalidParameterError):
            await service.get_overview(period="", specialization=None)

    async def test_all_invalid_specialization_ids_returns_all_data(
        self, service, mock_overview_repo
    ):
        """All invalid specialization IDs treated as no filter (returns all data).

        Validates: Requirements 1.7
        """
        mock_overview_repo.get_latest_by_specializations.return_value = []
        mock_overview_repo.get_status_distribution.return_value = []

        await service.get_overview(period=None, specialization="not-a-uuid,also-invalid")

        # Should be called with None (no filter)
        mock_overview_repo.get_latest_by_specializations.assert_called_once_with(None, 7)

    async def test_no_kpi_records_returns_zeros_with_null_trends(
        self, service, mock_overview_repo
    ):
        """No KPI history records returns all zeros with null trends.

        Validates: Requirements 1.10
        """
        mock_overview_repo.get_latest_by_specializations.return_value = []
        mock_overview_repo.get_status_distribution.return_value = []

        result = await service.get_overview(period=None, specialization=None)

        assert isinstance(result, OverviewData)
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
        record1 = _make_kpi_record(
            projects_count=10,
            projects_increase_count=2,
            projects_decrease_count=0,
            at_risk_count=3,
        )
        record2 = _make_kpi_record(
            projects_count=5,
            projects_increase_count=1,
            projects_decrease_count=0,
            at_risk_count=2,
        )
        mock_overview_repo.get_latest_by_specializations.return_value = [record1, record2]
        mock_overview_repo.get_status_distribution.return_value = []

        result = await service.get_overview(period=None, specialization=None)

        assert result.metrics.total_projects.count == 15
        assert result.metrics.total_projects.trend == "increase"
        assert result.metrics.total_projects.change == 3
        assert result.metrics.at_risk.count == 5

    async def test_period_validated_before_specialization(
        self, service, mock_overview_repo
    ):
        """Period is validated before specialization (fail fast).

        Validates: Requirements 1.4
        """
        with pytest.raises(InvalidParameterError) as exc_info:
            await service.get_overview(period="invalid", specialization="also-invalid")
        assert "period" in exc_info.value.message
        # Repos should never be called
        mock_overview_repo.get_latest_by_specializations.assert_not_called()

    async def test_returns_overview_data_type(
        self, service, mock_overview_repo
    ):
        """get_overview returns an OverviewData instance."""
        mock_overview_repo.get_latest_by_specializations.return_value = []
        mock_overview_repo.get_status_distribution.return_value = []

        result = await service.get_overview(period=None, specialization=None)

        assert isinstance(result, OverviewData)
        assert isinstance(result.metrics, OverviewMetrics)
        assert isinstance(result.status_distribution, StatusDistribution)


class TestStatusDistributionComputation:
    """Tests for status distribution percentage calculation via get_overview."""

    async def test_percentage_calculation(
        self, service, mock_overview_repo
    ):
        """Percentages are calculated correctly as (count/total)*100 rounded to 1 decimal.

        Validates: Requirements 3.3
        """
        mock_overview_repo.get_latest_by_specializations.return_value = []
        mock_overview_repo.get_status_distribution.return_value = [
            {"status_name": "Active", "count": 7},
            {"status_name": "Completed", "count": 3},
        ]

        result = await service.get_overview(period=None, specialization=None)

        breakdown = result.status_distribution.breakdown
        assert result.status_distribution.total == 10
        assert len(breakdown) == 2
        assert breakdown[0].status == "Active"
        assert breakdown[0].percentage == 70.0
        assert breakdown[1].status == "Completed"
        assert breakdown[1].percentage == 30.0

    async def test_zero_total_returns_zero_percentages(
        self, service, mock_overview_repo
    ):
        """When total is zero, all percentages are 0.0 (no division by zero).

        Validates: Requirements 3.4
        """
        mock_overview_repo.get_latest_by_specializations.return_value = []
        mock_overview_repo.get_status_distribution.return_value = [
            {"status_name": "Active", "count": 0},
            {"status_name": "Completed", "count": 0},
        ]

        result = await service.get_overview(period=None, specialization=None)

        assert result.status_distribution.total == 0
        for item in result.status_distribution.breakdown:
            assert item.percentage == 0.0

    async def test_single_status_gets_100_percent(
        self, service, mock_overview_repo
    ):
        """Single status with all projects gets 100.0%."""
        mock_overview_repo.get_latest_by_specializations.return_value = []
        mock_overview_repo.get_status_distribution.return_value = [
            {"status_name": "Active", "count": 15},
        ]

        result = await service.get_overview(period=None, specialization=None)

        assert result.status_distribution.total == 15
        assert result.status_distribution.breakdown[0].percentage == 100.0

    async def test_percentage_rounding_to_one_decimal(
        self, service, mock_overview_repo
    ):
        """Percentages are rounded to one decimal place.

        Validates: Requirements 3.3
        """
        mock_overview_repo.get_latest_by_specializations.return_value = []
        mock_overview_repo.get_status_distribution.return_value = [
            {"status_name": "Active", "count": 1},
            {"status_name": "Completed", "count": 2},
            {"status_name": "Inactive", "count": 3},
        ]

        result = await service.get_overview(period=None, specialization=None)

        # 1/6 = 16.666... → 16.7, 2/6 = 33.333... → 33.3, 3/6 = 50.0
        breakdown = result.status_distribution.breakdown
        assert breakdown[0].percentage == pytest.approx(16.7, abs=0.01)
        assert breakdown[1].percentage == pytest.approx(33.3, abs=0.01)
        assert breakdown[2].percentage == pytest.approx(50.0, abs=0.01)

    async def test_empty_distribution_returns_empty_breakdown(
        self, service, mock_overview_repo
    ):
        """Empty distribution data returns total 0 and empty breakdown."""
        mock_overview_repo.get_latest_by_specializations.return_value = []
        mock_overview_repo.get_status_distribution.return_value = []

        result = await service.get_overview(period=None, specialization=None)

        assert result.status_distribution.total == 0
        assert result.status_distribution.breakdown == []
