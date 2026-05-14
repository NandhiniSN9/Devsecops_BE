"""Unit tests for StatusRepository."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.repositories.status_repository import StatusRepository


@pytest.fixture
def mock_session():
    """Create a mock AsyncSession."""
    session = AsyncMock()
    return session


@pytest.fixture
def repository(mock_session):
    """Create a StatusRepository with a mock session."""
    return StatusRepository(session=mock_session)


class TestGetActiveStatuses:
    """Tests for StatusRepository.get_active_statuses method."""

    async def test_returns_active_statuses(self, repository, mock_session):
        """Test that active statuses are returned."""
        mock_status_1 = MagicMock()
        mock_status_1.status_name = "Active"
        mock_status_1.is_active = 1

        mock_status_2 = MagicMock()
        mock_status_2.status_name = "Completed"
        mock_status_2.is_active = 1

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_status_1, mock_status_2]
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        result = await repository.get_active_statuses()

        assert len(result) == 2
        assert result[0].status_name == "Active"
        assert result[1].status_name == "Completed"
        mock_session.execute.assert_awaited_once()

    async def test_returns_empty_list_when_no_active_statuses(self, repository, mock_session):
        """Test that an empty list is returned when no active statuses exist."""
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        result = await repository.get_active_statuses()

        assert result == []
        mock_session.execute.assert_awaited_once()

    async def test_returns_list_type(self, repository, mock_session):
        """Test that the return type is always a list."""
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        result = await repository.get_active_statuses()

        assert isinstance(result, list)
