"""Unit tests for ClientRepository (filters) data access operations."""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.filters_repository import ClientRepository
from src.repositories.schema.specialization import Specialization
from src.repositories.schema.status import Status


@pytest.fixture
def mock_session():
    """Create a mock async session."""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def repo(mock_session):
    """Create a ClientRepository with mock session."""
    return ClientRepository(mock_session)


class TestGetActiveSpecializations:
    """Tests for get_active_specializations method."""

    @pytest.mark.asyncio
    async def test_get_active_specializations_returns_list(self, repo, mock_session):
        """Should return list of active specializations."""
        specs = [
            Specialization(
                specialization_id=uuid.uuid4(),
                specialization_name="DevSecOps",
                is_active=1,
            ),
            Specialization(
                specialization_id=uuid.uuid4(),
                specialization_name="DevOps",
                is_active=1,
            ),
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = specs
        mock_session.execute.return_value = mock_result

        result = await repo.get_active_specializations()

        assert len(result) == 2
        assert result[0].specialization_name == "DevSecOps"
        assert result[1].specialization_name == "DevOps"

    @pytest.mark.asyncio
    async def test_get_active_specializations_empty(self, repo, mock_session):
        """Should return empty list when no active specializations."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        result = await repo.get_active_specializations()

        assert result == []


class TestGetActiveStatuses:
    """Tests for get_active_statuses method."""

    @pytest.mark.asyncio
    async def test_get_active_statuses_returns_list(self, repo, mock_session):
        """Should return list of active statuses."""
        statuses = [
            Status(status_id=uuid.uuid4(), status_name="Active", is_active=1),
            Status(status_id=uuid.uuid4(), status_name="Completed", is_active=1),
            Status(status_id=uuid.uuid4(), status_name="Inactive", is_active=1),
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = statuses
        mock_session.execute.return_value = mock_result

        result = await repo.get_active_statuses()

        assert len(result) == 3
        assert result[0].status_name == "Active"

    @pytest.mark.asyncio
    async def test_get_active_statuses_empty(self, repo, mock_session):
        """Should return empty list when no active statuses."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        result = await repo.get_active_statuses()

        assert result == []


class TestGetActiveClients:
    """Tests for get_active_clients method."""

    @pytest.mark.asyncio
    async def test_get_active_clients_returns_list(self, repo, mock_session):
        """Should return list of unique client names."""
        mock_result = MagicMock()
        mock_result.all.return_value = [("ClientA",), ("ClientB",), ("ClientC",)]
        mock_session.execute.return_value = mock_result

        result = await repo.get_active_clients()

        assert len(result) == 3
        assert result[0]["name"] == "ClientA"
        assert result[1]["name"] == "ClientB"
        # UUID should be consistent for same client name
        assert "id" in result[0]

    @pytest.mark.asyncio
    async def test_get_active_clients_empty(self, repo, mock_session):
        """Should return empty list when no clients."""
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.execute.return_value = mock_result

        result = await repo.get_active_clients()

        assert result == []

    @pytest.mark.asyncio
    async def test_get_active_clients_generates_consistent_uuids(self, repo, mock_session):
        """Should generate consistent UUIDs for same client names."""
        mock_result = MagicMock()
        mock_result.all.return_value = [("TestClient",)]
        mock_session.execute.return_value = mock_result

        # Call twice
        result1 = await repo.get_active_clients()

        mock_session.execute.return_value = mock_result  # Reset mock
        result2 = await repo.get_active_clients()

        # Same client name should produce same UUID
        assert result1[0]["id"] == result2[0]["id"]
