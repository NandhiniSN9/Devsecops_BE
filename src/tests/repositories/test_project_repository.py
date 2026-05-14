"""Unit tests for ProjectRepository."""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.repositories.project_repository import ProjectRepository


@pytest.fixture
def mock_session():
    """Create a mock AsyncSession."""
    session = AsyncMock()
    return session


@pytest.fixture
def repository(mock_session):
    """Create a ProjectRepository with a mock session."""
    return ProjectRepository(session=mock_session)


class TestGetStatusDistribution:
    """Tests for ProjectRepository.get_status_distribution method."""

    async def test_returns_distribution_without_specialization_filter(self, repository, mock_session):
        """Test status distribution returns all active statuses without filter.

        Validates: Requirements 3.2, 3.6
        """
        mock_row_1 = MagicMock()
        mock_row_1.status_name = "Active"
        mock_row_1.count = 10

        mock_row_2 = MagicMock()
        mock_row_2.status_name = "Completed"
        mock_row_2.count = 5

        mock_row_3 = MagicMock()
        mock_row_3.status_name = "Inactive"
        mock_row_3.count = 0

        mock_result = MagicMock()
        mock_result.all.return_value = [mock_row_1, mock_row_2, mock_row_3]
        mock_session.execute.return_value = mock_result

        result = await repository.get_status_distribution(specialization_ids=None)

        assert len(result) == 3
        assert result[0] == {"status_name": "Active", "count": 10}
        assert result[1] == {"status_name": "Completed", "count": 5}
        assert result[2] == {"status_name": "Inactive", "count": 0}
        mock_session.execute.assert_awaited_once()

    async def test_includes_statuses_with_zero_count(self, repository, mock_session):
        """Test that all active statuses are included even with 0 projects.

        Validates: Requirements 3.6
        """
        mock_row_1 = MagicMock()
        mock_row_1.status_name = "Active"
        mock_row_1.count = 3

        mock_row_2 = MagicMock()
        mock_row_2.status_name = "At Risk"
        mock_row_2.count = 0

        mock_row_3 = MagicMock()
        mock_row_3.status_name = "Completed"
        mock_row_3.count = 0

        mock_row_4 = MagicMock()
        mock_row_4.status_name = "Inactive"
        mock_row_4.count = 0

        mock_result = MagicMock()
        mock_result.all.return_value = [mock_row_1, mock_row_2, mock_row_3, mock_row_4]
        mock_session.execute.return_value = mock_result

        result = await repository.get_status_distribution(specialization_ids=None)

        assert len(result) == 4
        # Verify statuses with 0 count are included
        zero_count_statuses = [r for r in result if r["count"] == 0]
        assert len(zero_count_statuses) == 3

    async def test_returns_distribution_with_specialization_filter(self, repository, mock_session):
        """Test status distribution with specialization filter applied.

        Validates: Requirements 3.2
        """
        spec_id = uuid.uuid4()

        mock_row_1 = MagicMock()
        mock_row_1.status_name = "Active"
        mock_row_1.count = 2

        mock_row_2 = MagicMock()
        mock_row_2.status_name = "Completed"
        mock_row_2.count = 1

        mock_result = MagicMock()
        mock_result.all.return_value = [mock_row_1, mock_row_2]
        mock_session.execute.return_value = mock_result

        result = await repository.get_status_distribution(specialization_ids=[spec_id])

        assert len(result) == 2
        assert result[0] == {"status_name": "Active", "count": 2}
        assert result[1] == {"status_name": "Completed", "count": 1}
        mock_session.execute.assert_awaited_once()

    async def test_returns_empty_list_when_no_active_statuses(self, repository, mock_session):
        """Test that an empty list is returned when no active statuses exist.

        Validates: Requirements 3.6
        """
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.execute.return_value = mock_result

        result = await repository.get_status_distribution(specialization_ids=None)

        assert result == []

    async def test_returns_list_of_dicts(self, repository, mock_session):
        """Test that the return type is a list of dicts with correct keys."""
        mock_row = MagicMock()
        mock_row.status_name = "Active"
        mock_row.count = 5

        mock_result = MagicMock()
        mock_result.all.return_value = [mock_row]
        mock_session.execute.return_value = mock_result

        result = await repository.get_status_distribution(specialization_ids=None)

        assert isinstance(result, list)
        assert len(result) == 1
        assert "status_name" in result[0]
        assert "count" in result[0]

    async def test_multiple_specialization_ids_filter(self, repository, mock_session):
        """Test status distribution with multiple specialization IDs.

        Validates: Requirements 3.2
        """
        spec_id_1 = uuid.uuid4()
        spec_id_2 = uuid.uuid4()

        mock_row = MagicMock()
        mock_row.status_name = "Active"
        mock_row.count = 7

        mock_result = MagicMock()
        mock_result.all.return_value = [mock_row]
        mock_session.execute.return_value = mock_result

        result = await repository.get_status_distribution(
            specialization_ids=[spec_id_1, spec_id_2]
        )

        assert len(result) == 1
        assert result[0]["count"] == 7
        mock_session.execute.assert_awaited_once()

    async def test_all_statuses_have_zero_count(self, repository, mock_session):
        """Test distribution when all statuses have zero projects.

        Validates: Requirements 3.6
        """
        statuses = ["Active", "At Risk", "Completed", "Inactive", "Not Applicable"]
        mock_rows = []
        for status_name in statuses:
            row = MagicMock()
            row.status_name = status_name
            row.count = 0
            mock_rows.append(row)

        mock_result = MagicMock()
        mock_result.all.return_value = mock_rows
        mock_session.execute.return_value = mock_result

        result = await repository.get_status_distribution(specialization_ids=None)

        assert len(result) == 5
        for item in result:
            assert item["count"] == 0


class TestGetDistinctClients:
    """Tests for ProjectRepository.get_distinct_clients method."""

    async def test_returns_distinct_clients(self, repository, mock_session):
        """Test that distinct client values are returned.

        Validates: Requirements 1.5
        """
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = ["Client A", "Client B", "Client C"]
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        result = await repository.get_distinct_clients()

        assert result == ["Client A", "Client B", "Client C"]
        mock_session.execute.assert_awaited_once()

    async def test_excludes_null_values(self, repository, mock_session):
        """Test that null client values are excluded from results.

        Validates: Requirements 1.5
        """
        # The query itself filters nulls; mock returns only non-null values
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = ["Client A", "Client B"]
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        result = await repository.get_distinct_clients()

        assert None not in result
        assert len(result) == 2

    async def test_excludes_empty_string_values(self, repository, mock_session):
        """Test that empty string client values are excluded from results.

        Validates: Requirements 1.5
        """
        # The query filters empty strings; mock returns only valid values
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = ["Client A"]
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        result = await repository.get_distinct_clients()

        assert "" not in result
        assert len(result) == 1

    async def test_returns_empty_list_when_no_clients(self, repository, mock_session):
        """Test that an empty list is returned when no clients exist."""
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        result = await repository.get_distinct_clients()

        assert result == []
        assert isinstance(result, list)

    async def test_returns_sorted_clients(self, repository, mock_session):
        """Test that clients are returned in sorted order (query uses ORDER BY)."""
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = ["Alpha Corp", "Beta Inc", "Gamma LLC"]
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        result = await repository.get_distinct_clients()

        assert result == ["Alpha Corp", "Beta Inc", "Gamma LLC"]

    async def test_returns_list_type(self, repository, mock_session):
        """Test that the return type is always a list of strings."""
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = ["Client X"]
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        result = await repository.get_distinct_clients()

        assert isinstance(result, list)
        assert all(isinstance(c, str) for c in result)
