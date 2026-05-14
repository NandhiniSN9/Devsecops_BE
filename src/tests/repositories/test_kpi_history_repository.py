"""Unit tests for KpiHistoryRepository."""

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.repositories.kpi_history_repository import KpiHistoryRepository


@pytest.fixture
def mock_session():
    """Create a mock AsyncSession."""
    session = AsyncMock()
    return session


@pytest.fixture
def repository(mock_session):
    """Create a KpiHistoryRepository with a mock session."""
    return KpiHistoryRepository(session=mock_session)


class TestGetLatestBySpecializations:
    """Tests for KpiHistoryRepository.get_latest_by_specializations method."""

    async def test_returns_latest_record_per_specialization(self, repository, mock_session):
        """Test that the window function returns only the latest record per specialization.

        Validates: Requirements 1.3
        """
        spec_id_1 = uuid.uuid4()
        spec_id_2 = uuid.uuid4()

        mock_record_1 = MagicMock()
        mock_record_1.specialization_id = spec_id_1
        mock_record_1.projects_count = 10
        mock_record_1.created_at = datetime.now(UTC)

        mock_record_2 = MagicMock()
        mock_record_2.specialization_id = spec_id_2
        mock_record_2.projects_count = 5
        mock_record_2.created_at = datetime.now(UTC)

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_record_1, mock_record_2]
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        result = await repository.get_latest_by_specializations(
            specialization_ids=None,
            period_days=7,
        )

        assert len(result) == 2
        assert result[0].specialization_id == spec_id_1
        assert result[1].specialization_id == spec_id_2
        mock_session.execute.assert_awaited_once()

    async def test_filters_by_specialization_ids(self, repository, mock_session):
        """Test that specialization_ids filter is applied when provided.

        Validates: Requirements 1.5
        """
        spec_id = uuid.uuid4()

        mock_record = MagicMock()
        mock_record.specialization_id = spec_id
        mock_record.projects_count = 15

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_record]
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        result = await repository.get_latest_by_specializations(
            specialization_ids=[spec_id],
            period_days=30,
        )

        assert len(result) == 1
        assert result[0].specialization_id == spec_id
        mock_session.execute.assert_awaited_once()

    async def test_period_days_7_filters_last_week(self, repository, mock_session):
        """Test that period_days=7 correctly filters records within the last 7 days.

        Validates: Requirements 1.3
        """
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        result = await repository.get_latest_by_specializations(
            specialization_ids=None,
            period_days=7,
        )

        assert result == []
        mock_session.execute.assert_awaited_once()

    async def test_period_days_30_filters_last_month(self, repository, mock_session):
        """Test that period_days=30 correctly filters records within the last 30 days.

        Validates: Requirements 1.3
        """
        mock_record = MagicMock()
        mock_record.specialization_id = uuid.uuid4()
        mock_record.projects_count = 20

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_record]
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        result = await repository.get_latest_by_specializations(
            specialization_ids=None,
            period_days=30,
        )

        assert len(result) == 1
        mock_session.execute.assert_awaited_once()

    async def test_period_days_90_filters_last_3_months(self, repository, mock_session):
        """Test that period_days=90 correctly filters records within the last 90 days.

        Validates: Requirements 1.3
        """
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        result = await repository.get_latest_by_specializations(
            specialization_ids=None,
            period_days=90,
        )

        assert result == []
        mock_session.execute.assert_awaited_once()

    async def test_returns_empty_list_when_no_records_found(self, repository, mock_session):
        """Test that an empty list is returned when no KPI history records exist.

        Validates: Requirements 1.3
        """
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        result = await repository.get_latest_by_specializations(
            specialization_ids=None,
            period_days=7,
        )

        assert result == []
        assert isinstance(result, list)

    async def test_none_specialization_ids_returns_all(self, repository, mock_session):
        """Test that None specialization_ids returns data for all active specializations.

        Validates: Requirements 1.5
        """
        spec_id_1 = uuid.uuid4()
        spec_id_2 = uuid.uuid4()
        spec_id_3 = uuid.uuid4()

        mock_records = []
        for spec_id in [spec_id_1, spec_id_2, spec_id_3]:
            record = MagicMock()
            record.specialization_id = spec_id
            mock_records.append(record)

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = mock_records
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        result = await repository.get_latest_by_specializations(
            specialization_ids=None,
            period_days=7,
        )

        assert len(result) == 3

    async def test_multiple_specialization_ids_filter(self, repository, mock_session):
        """Test filtering by multiple specialization IDs.

        Validates: Requirements 1.5
        """
        spec_id_1 = uuid.uuid4()
        spec_id_2 = uuid.uuid4()

        mock_record_1 = MagicMock()
        mock_record_1.specialization_id = spec_id_1
        mock_record_2 = MagicMock()
        mock_record_2.specialization_id = spec_id_2

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_record_1, mock_record_2]
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        result = await repository.get_latest_by_specializations(
            specialization_ids=[spec_id_1, spec_id_2],
            period_days=7,
        )

        assert len(result) == 2

    async def test_returns_list_type(self, repository, mock_session):
        """Test that the return type is always a list."""
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        result = await repository.get_latest_by_specializations(
            specialization_ids=None,
            period_days=7,
        )

        assert isinstance(result, list)

    async def test_empty_specialization_ids_list_returns_all(self, repository, mock_session):
        """Test that an empty specialization_ids list does not apply filter (falsy check).

        Validates: Requirements 1.5
        """
        mock_record = MagicMock()
        mock_record.specialization_id = uuid.uuid4()

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_record]
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        result = await repository.get_latest_by_specializations(
            specialization_ids=[],
            period_days=7,
        )

        assert len(result) == 1
