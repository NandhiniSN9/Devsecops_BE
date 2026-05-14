"""Unit tests for SpecializationRepository."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.repositories.specialization_repository import SpecializationRepository


@pytest.fixture
def mock_session():
    """Create a mock AsyncSession."""
    session = AsyncMock()
    return session


@pytest.fixture
def repository(mock_session):
    """Create a SpecializationRepository with a mock session."""
    return SpecializationRepository(session=mock_session)


class TestGetActiveSpecializations:
    """Tests for SpecializationRepository.get_active_specializations method."""

    async def test_returns_active_specializations(self, repository, mock_session):
        """Test that active specializations are returned."""
        mock_spec_1 = MagicMock()
        mock_spec_1.specialization_name = "Backend"
        mock_spec_1.is_active = 1

        mock_spec_2 = MagicMock()
        mock_spec_2.specialization_name = "Frontend"
        mock_spec_2.is_active = 1

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_spec_1, mock_spec_2]
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        result = await repository.get_active_specializations()

        assert len(result) == 2
        assert result[0].specialization_name == "Backend"
        assert result[1].specialization_name == "Frontend"
        mock_session.execute.assert_awaited_once()

    async def test_returns_empty_list_when_no_active_specializations(self, repository, mock_session):
        """Test that an empty list is returned when no active specializations exist."""
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        result = await repository.get_active_specializations()

        assert result == []
        mock_session.execute.assert_awaited_once()

    async def test_returns_list_type(self, repository, mock_session):
        """Test that the return type is always a list."""
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        result = await repository.get_active_specializations()

        assert isinstance(result, list)
