"""Unit tests for OverviewService.

Tests cover the public get_overview() method and internal helpers:
_build_tile(), _validate_period(), _parse_specialization(), _build_metrics().
"""

import uuid
from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from src.models.response.overview_response import (
    OverviewDataResponse,
    OverviewMetricsResponse,
    StatusDistributionResponse,
)
from src.repositories.overview_repository import OverviewRepository
from src.services.overview_service import OverviewService
from src.utils.exceptions.exceptions import InvalidParameterError


@pytest.fixture
def mock_overview_repo():
    """Create a mock OverviewRepository."""
    return AsyncMock(spec=OverviewRepository)


@pytest.fixture
def service(mock_overview_repo):
    """Create an OverviewService with mocked repository."""
    return OverviewService(overview_repo=mock_overview_repo)


class TestValidatePeriod:
    """Tests for OverviewService._validate_period."""

    def test_none_defaults_to_last_week(self, service):
        """When period is None, defaults to 'last_week'."""
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
        """Invalid period value raises InvalidParameterError."""
        with pytest.raises(InvalidParameterError) as exc_info:
            service._validate_period("last_year")
        assert "period" in exc_info.value.message
        assert "last_week" in exc_info.value.message

    def test_empty_string_raises_error(self, service):
        """Empty string period raises InvalidParameterError."""
        with pytest.raises(InvalidParameterError) as exc_info:
            service._validate_period("")
        assert "period" in exc_info.value.message

    def test_case_sensitive_validation(self, service):
        """Period validation is case-sensitive; 'Last_Week' is invalid."""
        with pytest.raises(InvalidParameterError):
            service._validate_period("Last_Week")


class TestParseSpecialization:
    """Tests for OverviewService._parse_specialization."""

    def test_none_returns_none(self, service):
        """When specialization is None, returns None."""
        result = service._parse_specialization(None)
        assert result is None

    def test_empty_string_returns_none(self, service):
        """When specialization is empty string, returns None."""
        result = service._parse_specialization("")
        assert result is None

    def test_whitespace_only_returns_none(self, service):
        """When specialization is whitespace only, returns None."""
        result = service._parse_specialization("   ")
        assert result is None

    def test_valid_single_uuid_parsed(self, service):
        """Single valid UUID is parsed correctly."""
        test_uuid = uuid.uuid4()
        result = service._parse_specialization(str(test_uuid))
        assert result == [test_uuid]

    def test_valid_multiple_uuids_parsed(self, service):
        """Multiple valid UUIDs are parsed correctly."""
        uuid1 = uuid.uuid4()
        uuid2 = uuid.uuid4()
        result = service._parse_specialization(f"{uuid1},{uuid2}")
        assert result == [uuid1, uuid2]

    def test_invalid_uuids_skipped(self, service):
        """Invalid UUIDs are skipped, returns None if all invalid."""
        result = service._parse_specialization("not-a-uuid,also-invalid")
        assert result is None

    def test_mixed_valid_and_invalid_uuids(self, service):
        """Mix of valid and invalid UUIDs returns only valid ones."""
        valid_uuid = uuid.uuid4()
        result = service._parse_specialization(f"{valid_uuid},not-valid,also-bad")
        assert result == [valid_uuid]

    def test_limits_to_50_uuids(self, service):
        """Limits parsing to MAX_SPECIALIZATION_FILTER_COUNT (50) UUIDs."""
        uuids = [str(uuid.uuid4()) for _ in range(60)]
        csv = ",".join(uuids)
        result = service._parse_specialization(csv)
        assert len(result) == 50

    def test_whitespace_around_uuids_trimmed(self, service):
        """Whitespace around UUIDs is trimmed."""
        test_uuid = uuid.uuid4()
        result = service._parse_specialization(f"  {test_uuid}  ")
        assert result == [test_uuid]


class TestBuildTile:
    """Tests for OverviewService._build_tile static method."""

    def test_increase(self):
        """When current > comparison, trend is 'increase'."""
        tile = OverviewService._build_tile(5, 0)
        assert tile.trend == "increase"
        assert tile.change == 5
        assert tile.count == 5

    def test_decrease(self):
        """When current < comparison, trend is 'decrease'."""
        tile = OverviewService._build_tile(2, 5)
        assert tile.trend == "decrease"
        assert tile.change == 3
        assert tile.count == 2

    def test_flat(self):
        """When current == comparison, trend is 'flat'."""
        tile = OverviewService._build_tile(5, 5)
        assert tile.trend == "flat"
        assert tile.change == 0
        assert tile.count == 5

    def test_both_zero_is_flat(self):
        """When both are 0, trend is 'flat' with change 0."""
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

    async def test_no_data_returns_zeros_with_null_trends(
        self, service, mock_overview_repo
    ):
        """No data returns all zeros with null trends."""
        mock_overview_repo.get_last_synced.return_value = None
        mock_overview_repo.is_sync_in_progress.return_value = False
        mock_overview_repo.get_live_counts.return_value = {
            "total_projects": 0,
            "adopted": 0,
            "completed": 0,
            "active": 0,
            "inactive": 0,
            "at_risk": 0,
            "not_applicable": 0,
        }
        mock_overview_repo.get_historical_counts.return_value = None

        result = await service.get_overview(period=None, specialization=None)

        assert isinstance(result, OverviewDataResponse)
        metrics = result.metrics
        for tile in [
            metrics.total_projects,
            metrics.adopted,
            metrics.completed,
            metrics.active,
            metrics.inactive,
            metrics.at_risk,
            metrics.not_applicable,
        ]:
            assert tile.count == 0
            assert tile.trend is None
            assert tile.change == 0

    async def test_with_historical_data_shows_trends(
        self, service, mock_overview_repo
    ):
        """With historical data, trends are calculated correctly."""
        mock_overview_repo.get_last_synced.return_value = datetime(2026, 5, 18, 9, 30)
        mock_overview_repo.is_sync_in_progress.return_value = False
        mock_overview_repo.get_live_counts.return_value = {
            "total_projects": 10,
            "adopted": 4,
            "completed": 3,
            "active": 2,
            "inactive": 1,
            "at_risk": 0,
            "not_applicable": 0,
        }
        mock_overview_repo.get_historical_counts.return_value = {
            "total_projects": 8,
            "adopted": 3,
            "completed": 3,
            "active": 1,
            "inactive": 1,
            "at_risk": 1,
            "not_applicable": 0,
        }

        result = await service.get_overview(period="last_week", specialization=None)

        assert result.metrics.total_projects.count == 10
        assert result.metrics.total_projects.trend == "increase"
        assert result.metrics.total_projects.change == 2
        assert result.metrics.adopted.count == 4
        assert result.metrics.adopted.trend == "increase"
        assert result.metrics.adopted.change == 1
        assert result.metrics.completed.trend == "flat"
        assert result.metrics.at_risk.trend == "decrease"
        assert result.metrics.at_risk.change == 1

    async def test_adopted_count_included_in_metrics(
        self, service, mock_overview_repo
    ):
        """Adopted count is included as one of the 7 metrics."""
        mock_overview_repo.get_last_synced.return_value = None
        mock_overview_repo.is_sync_in_progress.return_value = False
        mock_overview_repo.get_live_counts.return_value = {
            "total_projects": 15,
            "adopted": 7,
            "completed": 3,
            "active": 3,
            "inactive": 1,
            "at_risk": 1,
            "not_applicable": 0,
        }
        mock_overview_repo.get_historical_counts.return_value = None

        result = await service.get_overview(period=None, specialization=None)

        assert result.metrics.adopted.count == 7
        assert result.metrics.adopted.trend is None

    async def test_invalid_period_raises_error(self, service):
        """Invalid period raises InvalidParameterError before querying repos."""
        with pytest.raises(InvalidParameterError):
            await service.get_overview(period="invalid")

    async def test_empty_period_raises_error(self, service):
        """Empty period string raises InvalidParameterError."""
        with pytest.raises(InvalidParameterError):
            await service.get_overview(period="")

    async def test_specialization_filter_passed_to_repo(
        self, service, mock_overview_repo
    ):
        """Specialization filter is parsed and passed to get_live_counts."""
        test_uuid = uuid.uuid4()
        mock_overview_repo.get_last_synced.return_value = None
        mock_overview_repo.is_sync_in_progress.return_value = False
        mock_overview_repo.get_live_counts.return_value = {
            "total_projects": 0,
            "adopted": 0,
            "completed": 0,
            "active": 0,
            "inactive": 0,
            "at_risk": 0,
            "not_applicable": 0,
        }
        mock_overview_repo.get_historical_counts.return_value = None

        await service.get_overview(period=None, specialization=str(test_uuid))

        mock_overview_repo.get_live_counts.assert_called_once_with([test_uuid])

    async def test_returns_overview_data_type(
        self, service, mock_overview_repo
    ):
        """get_overview returns an OverviewDataResponse instance."""
        mock_overview_repo.get_last_synced.return_value = None
        mock_overview_repo.is_sync_in_progress.return_value = False
        mock_overview_repo.get_live_counts.return_value = {
            "total_projects": 0,
            "adopted": 0,
            "completed": 0,
            "active": 0,
            "inactive": 0,
            "at_risk": 0,
            "not_applicable": 0,
        }
        mock_overview_repo.get_historical_counts.return_value = None

        result = await service.get_overview(period=None)

        assert isinstance(result, OverviewDataResponse)
        assert isinstance(result.metrics, OverviewMetricsResponse)
        assert isinstance(result.status_distribution, StatusDistributionResponse)

    async def test_sync_detail_populated(
        self, service, mock_overview_repo
    ):
        """Sync detail is populated with last_sync_datetime and is_sync_in_progress."""
        mock_overview_repo.get_last_synced.return_value = datetime(2026, 5, 18, 9, 30)
        mock_overview_repo.is_sync_in_progress.return_value = True
        mock_overview_repo.get_live_counts.return_value = {
            "total_projects": 0,
            "adopted": 0,
            "completed": 0,
            "active": 0,
            "inactive": 0,
            "at_risk": 0,
            "not_applicable": 0,
        }
        mock_overview_repo.get_historical_counts.return_value = None

        result = await service.get_overview(period=None)

        assert result.sync_detail.last_sync_datetime == "18 May 2026, 09:30"
        assert result.sync_detail.is_sync_in_progress is True


class TestStatusDistributionComputation:
    """Tests for status distribution percentage calculation."""

    async def test_percentage_calculation(self, service, mock_overview_repo):
        """Percentages are calculated correctly as (count/total)*100 rounded to 1 decimal."""
        mock_overview_repo.get_last_synced.return_value = None
        mock_overview_repo.is_sync_in_progress.return_value = False
        mock_overview_repo.get_live_counts.return_value = {
            "total_projects": 10,
            "adopted": 4,
            "completed": 3,
            "active": 2,
            "inactive": 1,
            "at_risk": 0,
            "not_applicable": 0,
        }
        mock_overview_repo.get_historical_counts.return_value = None

        result = await service.get_overview(period=None)

        breakdown = result.status_distribution.breakdown
        assert result.status_distribution.total == 10
        adopted_item = next(b for b in breakdown if b.status == "Adopted")
        active_item = next(b for b in breakdown if b.status == "Active")
        assert adopted_item.percentage == 40.0
        assert active_item.percentage == 20.0

    async def test_zero_total_returns_zero_percentages(self, service, mock_overview_repo):
        """When total is zero, all percentages are 0.0 (no division by zero)."""
        mock_overview_repo.get_last_synced.return_value = None
        mock_overview_repo.is_sync_in_progress.return_value = False
        mock_overview_repo.get_live_counts.return_value = {
            "total_projects": 0,
            "adopted": 0,
            "completed": 0,
            "active": 0,
            "inactive": 0,
            "at_risk": 0,
            "not_applicable": 0,
        }
        mock_overview_repo.get_historical_counts.return_value = None

        result = await service.get_overview(period=None)

        assert result.status_distribution.total == 0
        for item in result.status_distribution.breakdown:
            assert item.percentage == 0.0

    async def test_percentage_rounding_to_one_decimal(self, service, mock_overview_repo):
        """Percentages are rounded to one decimal place."""
        mock_overview_repo.get_last_synced.return_value = None
        mock_overview_repo.is_sync_in_progress.return_value = False
        mock_overview_repo.get_live_counts.return_value = {
            "total_projects": 6,
            "adopted": 0,
            "completed": 2,
            "active": 1,
            "inactive": 3,
            "at_risk": 0,
            "not_applicable": 0,
        }
        mock_overview_repo.get_historical_counts.return_value = None

        result = await service.get_overview(period=None)

        breakdown = result.status_distribution.breakdown
        active_item = next(b for b in breakdown if b.status == "Active")
        completed_item = next(b for b in breakdown if b.status == "Completed")
        inactive_item = next(b for b in breakdown if b.status == "Inactive")
        # 1/6 = 16.7, 2/6 = 33.3, 3/6 = 50.0
        assert active_item.percentage == pytest.approx(16.7, abs=0.01)
        assert completed_item.percentage == pytest.approx(33.3, abs=0.01)
        assert inactive_item.percentage == pytest.approx(50.0, abs=0.01)
