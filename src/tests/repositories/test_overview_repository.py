"""Unit tests for OverviewRepository data access operations."""

import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.overview_repository import OverviewRepository
from src.repositories.schema.kpi_history import KpiHistory
from src.repositories.schema.project import Project
from src.repositories.schema.setting import Setting
from src.repositories.schema.specialization import Specialization
from src.repositories.schema.status import Status


@pytest.fixture
def mock_session():
    """Create a mock async session."""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def repo(mock_session):
    """Create an OverviewRepository with mock session."""
    return OverviewRepository(mock_session)


class TestGetLiveCounts:
    """Tests for get_live_counts method."""

    @pytest.mark.asyncio
    async def test_get_live_counts_no_filter(self, repo, mock_session):
        """Should return live counts without specialization filter."""
        # Mock total projects
        total_result = MagicMock()
        total_result.scalar_one.return_value = 100

        # Mock adopted count
        adopted_result = MagicMock()
        adopted_result.scalar_one.return_value = 40

        # Mock status counts
        status_result = MagicMock()
        status_result.all.return_value = [
            ("Completed", 30),
            ("Active", 25),
            ("Inactive", 20),
            ("At Risk", 15),
            ("Not Applicable", 10),
        ]

        mock_session.execute.side_effect = [total_result, adopted_result, status_result]

        result = await repo.get_live_counts(specialization_ids=None)

        assert result["total_projects"] == 100
        assert result["adopted"] == 40
        assert result["completed"] == 30
        assert result["active"] == 25
        assert result["inactive"] == 20
        assert result["at_risk"] == 15
        assert result["not_applicable"] == 10

    @pytest.mark.asyncio
    async def test_get_live_counts_with_specialization_filter(self, repo, mock_session):
        """Should filter by specialization IDs."""
        spec_ids = [uuid.uuid4(), uuid.uuid4()]

        total_result = MagicMock()
        total_result.scalar_one.return_value = 50
        adopted_result = MagicMock()
        adopted_result.scalar_one.return_value = 20
        status_result = MagicMock()
        status_result.all.return_value = []

        mock_session.execute.side_effect = [total_result, adopted_result, status_result]

        result = await repo.get_live_counts(specialization_ids=spec_ids)

        assert result["total_projects"] == 50
        assert result["adopted"] == 20


class TestGetHistoricalCounts:
    """Tests for get_historical_counts method."""

    @pytest.mark.asyncio
    async def test_get_historical_counts_found(self, repo, mock_session):
        """Should return historical KPI counts from kpi_history."""
        spec_ids = [uuid.uuid4()]
        days_ago = 7

        mock_kpi = KpiHistory(
            kpi_history_id=uuid.uuid4(),
            specialization_id=spec_ids[0],
            total_projects_count=90,
            adopted_count=35,
            completed_count=28,
            active_count=20,
            inactive_count=18,
            at_risk_count=12,
            not_applicable_count=9,
            snapshot_date=datetime.utcnow().date() - timedelta(days=days_ago),
        )

        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = mock_kpi
        mock_session.execute.return_value = mock_result

        result = await repo.get_historical_counts(days_ago, spec_ids)

        assert result["total_projects"] == 90
        assert result["adopted"] == 35
        assert result["completed"] == 28

    @pytest.mark.asyncio
    async def test_get_historical_counts_not_found(self, repo, mock_session):
        """Should return None when no historical data found."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_session.execute.return_value = mock_result

        result = await repo.get_historical_counts(7, [uuid.uuid4()])

        assert result is None


class TestGetStatusDistribution:
    """Tests for get_status_distribution method."""

    @pytest.mark.asyncio
    async def test_get_status_distribution_success(self, repo, mock_session):
        """Should return status distribution with percentages."""
        mock_result = MagicMock()
        mock_result.all.return_value = [
            ("Completed", 30),
            ("Active", 25),
            ("Inactive", 20),
        ]
        mock_session.execute.return_value = mock_result

        result = await repo.get_status_distribution(specialization_ids=None)

        assert result["total"] == 75
        assert len(result["breakdown"]) == 3
        assert result["breakdown"][0]["status"] == "Completed"
        assert result["breakdown"][0]["count"] == 30
        assert result["breakdown"][0]["percentage"] == pytest.approx(40.0)


class TestGetLastSyncDatetime:
    """Tests for get_last_sync_datetime method."""

    @pytest.mark.asyncio
    async def test_get_last_sync_datetime_found(self, repo, mock_session):
        """Should return formatted last sync datetime."""
        last_synced = datetime(2026, 5, 20, 14, 30, 0)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = last_synced
        mock_session.execute.return_value = mock_result

        result = await repo.get_last_sync_datetime([uuid.uuid4()])

        assert result == "20 May 2026, 14:30"

    @pytest.mark.asyncio
    async def test_get_last_sync_datetime_not_found(self, repo, mock_session):
        """Should return None when no sync datetime found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await repo.get_last_sync_datetime([uuid.uuid4()])

        assert result is None


class TestIsSyncInProgress:
    """Tests for is_sync_in_progress method."""

    @pytest.mark.asyncio
    async def test_is_sync_in_progress_true(self, repo, mock_session):
        """Should return True when sync is in progress."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = 1
        mock_session.execute.return_value = mock_result

        result = await repo.is_sync_in_progress([uuid.uuid4()])

        assert result is True

    @pytest.mark.asyncio
    async def test_is_sync_in_progress_false(self, repo, mock_session):
        """Should return False when no sync in progress."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await repo.is_sync_in_progress([uuid.uuid4()])

        assert result is False


class TestGetAtRiskThreshold:
    """Tests for get_at_risk_threshold method."""

    @pytest.mark.asyncio
    async def test_get_at_risk_threshold_single_specialization(self, repo, mock_session):
        """Should return threshold for single specialization."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = 30
        mock_session.execute.return_value = mock_result

        result = await repo.get_at_risk_threshold([uuid.uuid4()])

        assert result == 30

    @pytest.mark.asyncio
    async def test_get_at_risk_threshold_multiple_specializations(self, repo, mock_session):
        """Should return max threshold for multiple specializations."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = 45
        mock_session.execute.return_value = mock_result

        result = await repo.get_at_risk_threshold([uuid.uuid4(), uuid.uuid4()])

        assert result == 45

    @pytest.mark.asyncio
    async def test_get_at_risk_threshold_default(self, repo, mock_session):
        """Should return default 30 when no threshold found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await repo.get_at_risk_threshold([uuid.uuid4()])

        assert result == 30
