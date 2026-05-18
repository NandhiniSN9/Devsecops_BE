"""Tests for ServiceNowRepository data access operations."""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.schema.project import Project
from src.repositories.schema.repository import Repository
from src.repositories.schema.specialization import Specialization
from src.repositories.schema.status import Status
from src.repositories.servicenow_repository import ServiceNowRepository


@pytest.fixture
def mock_session():
    """Create a mock async session."""
    session = AsyncMock(spec=AsyncSession)
    return session


@pytest.fixture
def repo(mock_session):
    """Create a ServiceNowRepository with mock session."""
    return ServiceNowRepository(mock_session)


class TestGetProjectBySnProjectId:
    """Tests for get_project_by_sn_project_id method."""

    @pytest.mark.asyncio
    async def test_returns_project_when_found(self, repo, mock_session):
        """Should return project when sn_project_id matches."""
        project = Project(
            project_id=uuid.uuid4(),
            sn_project_id="SN-001",
            project_name="Test",
            onboarded_date="2026-01-01",
            project_type="Infra",
        )
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = project
        mock_session.execute.return_value = mock_result

        result = await repo.get_project_by_sn_project_id("SN-001")

        assert result is not None
        assert result.sn_project_id == "SN-001"

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self, repo, mock_session):
        """Should return None when sn_project_id doesn't exist."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await repo.get_project_by_sn_project_id("NONEXISTENT")

        assert result is None


class TestGetProjectByName:
    """Tests for get_project_by_name method."""

    @pytest.mark.asyncio
    async def test_returns_project_when_found(self, repo, mock_session):
        """Should return project when name matches (case-insensitive)."""
        project = Project(
            project_id=uuid.uuid4(),
            sn_project_id="SN-001",
            project_name="Test Project",
            onboarded_date="2026-01-01",
            project_type="Infra",
        )
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = project
        mock_session.execute.return_value = mock_result

        result = await repo.get_project_by_name("Test Project")

        assert result is not None
        assert result.project_name == "Test Project"

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self, repo, mock_session):
        """Should return None when project name doesn't exist."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_session.execute.return_value = mock_result

        result = await repo.get_project_by_name("Nonexistent")

        assert result is None


class TestGetInactiveStatus:
    """Tests for get_inactive_status method."""

    @pytest.mark.asyncio
    async def test_returns_inactive_status(self, repo, mock_session):
        """Should return the Inactive status record."""
        status = Status(status_id=uuid.uuid4(), status_name="Inactive", is_active=1)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = status
        mock_session.execute.return_value = mock_result

        result = await repo.get_inactive_status()

        assert result is not None
        assert result.status_name == "Inactive"

    @pytest.mark.asyncio
    async def test_returns_none_when_no_inactive_status(self, repo, mock_session):
        """Should return None when Inactive status doesn't exist."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await repo.get_inactive_status()

        assert result is None


class TestGetSpecializationByName:
    """Tests for get_specialization_by_name method."""

    @pytest.mark.asyncio
    async def test_returns_specialization_when_found(self, repo, mock_session):
        """Should return specialization when name matches."""
        spec = Specialization(
            specialization_id=uuid.uuid4(), specialization_name="DevSecOps", is_active=1
        )
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = spec
        mock_session.execute.return_value = mock_result

        result = await repo.get_specialization_by_name("DevSecOps")

        assert result is not None
        assert result.specialization_name == "DevSecOps"

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self, repo, mock_session):
        """Should return None when specialization doesn't exist."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await repo.get_specialization_by_name("Unknown")

        assert result is None


class TestCreateProject:
    """Tests for create_project method."""

    @pytest.mark.asyncio
    async def test_creates_project_successfully(self, repo, mock_session):
        """Should add project to session and flush."""
        project = Project(
            project_id=uuid.uuid4(),
            sn_project_id="SN-001",
            project_name="New Project",
            onboarded_date="2026-01-01",
            project_type="Infra",
        )

        result = await repo.create_project(project)

        mock_session.add.assert_called_once_with(project)
        mock_session.flush.assert_called_once()
        assert result == project


class TestCreateTicket:
    """Tests for create_ticket method."""

    @pytest.mark.asyncio
    async def test_creates_ticket_successfully(self, repo, mock_session):
        """Should add ticket to session and flush."""
        from src.repositories.schema.devsecops_ticket import DevsecopsTicket

        ticket = DevsecopsTicket(
            ticket_id=uuid.uuid4(),
            specialization_id=uuid.uuid4(),
            project_id=uuid.uuid4(),
            project_name="Test",
            is_active=1,
        )

        result = await repo.create_ticket(ticket)

        mock_session.add.assert_called_once_with(ticket)
        mock_session.flush.assert_called_once()
        assert result == ticket


class TestGetRepositoryByNameAndTicket:
    """Tests for get_repository_by_name_and_ticket method."""

    @pytest.mark.asyncio
    async def test_returns_repository_when_found(self, repo, mock_session):
        """Should return repository when name + ticket_id matches."""
        ticket_id = uuid.uuid4()
        repository = Repository(
            repository_id=uuid.uuid4(),
            ticket_id=ticket_id,
            repository_name="payments-api",
            is_active=1,
        )
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = repository
        mock_session.execute.return_value = mock_result

        result = await repo.get_repository_by_name_and_ticket("payments-api", ticket_id)

        assert result is not None
        assert result.repository_name == "payments-api"

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self, repo, mock_session):
        """Should return None when repository doesn't exist."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await repo.get_repository_by_name_and_ticket("nonexistent", uuid.uuid4())

        assert result is None


class TestCommit:
    """Tests for commit method."""

    @pytest.mark.asyncio
    async def test_commits_session(self, repo, mock_session):
        """Should call commit on the session."""
        await repo.commit()

        mock_session.commit.assert_called_once()
