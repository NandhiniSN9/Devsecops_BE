"""Tests for ServiceNowService business logic."""

import uuid
from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.models.servicenow_models import (
    RepositoryItem,
    SyncDevSecOpsTicketItem,
    SyncDevSecOpsTicketsRequest,
    SyncProjectItem,
    SyncProjectRequest,
)
from src.repositories.schema.project import Project
from src.repositories.schema.specialization import Specialization
from src.repositories.schema.status import Status
from src.repositories.servicenow_repository import ServiceNowRepository
from src.services.servicenow_service import ServiceNowService


@pytest.fixture
def mock_repo():
    """Create a mock ServiceNowRepository."""
    repo = AsyncMock(spec=ServiceNowRepository)
    repo.commit = AsyncMock()
    return repo


@pytest.fixture
def service(mock_repo):
    """Create a ServiceNowService with mocked repository."""
    return ServiceNowService(servicenow_repo=mock_repo)


@pytest.fixture
def sample_project_request():
    """Create a sample project sync request."""
    return SyncProjectRequest(
        projects=[
            SyncProjectItem(
                sn_project_id="SN-PRJ-001",
                project_name="Test Project",
                onboarded_date=date(2026, 3, 15),
                project_type="Infrastructure",
                specialization_name="DevSecOps",
                is_applicable=True,
                client="ABN AMRO",
                approver="approver@zeb.co",
            )
        ]
    )


@pytest.fixture
def sample_ticket_request():
    """Create a sample ticket sync request."""
    return SyncDevSecOpsTicketsRequest(
        tickets=[
            SyncDevSecOpsTicketItem(
                sn_project_id="SN-PRJ-001",
                project_name="Test Project",
                client="ABN AMRO",
                specialization_name="DevSecOps",
                repositories=[
                    RepositoryItem(
                        repo_name="payments-api",
                        ado_repo_id="ado-001",
                        lead_approvers=["lead1@zeb.co", "lead2@zeb.co"],
                    )
                ],
                requested_by="requester@zeb.co",
                approver="approver@zeb.co",
                requested_at=datetime(2026, 4, 15, 9, 0, 0),
            )
        ]
    )


class TestSyncProjects:
    """Tests for sync_projects method."""

    @pytest.mark.asyncio
    async def test_sync_projects_creates_new_project(self, service, mock_repo, sample_project_request):
        """Should create a new project when sn_project_id doesn't exist."""
        mock_repo.get_inactive_status.return_value = Status(
            status_id=uuid.uuid4(), status_name="Inactive", is_active=1
        )
        mock_repo.get_project_by_sn_project_id.return_value = None
        mock_repo.create_project.return_value = MagicMock()

        result = await service.sync_projects(sample_project_request, "servicenow@zeb.co")

        assert result["created"] == 1
        assert result["updated"] == 0
        assert result["total"] == 1
        mock_repo.create_project.assert_called_once()
        mock_repo.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_sync_projects_updates_existing_project(self, service, mock_repo, sample_project_request):
        """Should update project when sn_project_id already exists."""
        existing_project = Project(
            project_id=uuid.uuid4(),
            sn_project_id="SN-PRJ-001",
            project_name="Old Name",
            onboarded_date=date(2026, 1, 1),
            project_type="Old Type",
        )
        mock_repo.get_inactive_status.return_value = Status(
            status_id=uuid.uuid4(), status_name="Inactive", is_active=1
        )
        mock_repo.get_project_by_sn_project_id.return_value = existing_project
        mock_repo.update_project.return_value = existing_project

        result = await service.sync_projects(sample_project_request, "servicenow@zeb.co")

        assert result["created"] == 0
        assert result["updated"] == 1
        mock_repo.update_project.assert_called_once()
        mock_repo.create_project.assert_not_called()

    @pytest.mark.asyncio
    async def test_sync_projects_assigns_inactive_status(self, service, mock_repo, sample_project_request):
        """Should assign Inactive status to new projects."""
        inactive_id = uuid.uuid4()
        mock_repo.get_inactive_status.return_value = Status(
            status_id=inactive_id, status_name="Inactive", is_active=1
        )
        mock_repo.get_project_by_sn_project_id.return_value = None
        mock_repo.create_project.return_value = MagicMock()

        await service.sync_projects(sample_project_request, "servicenow@zeb.co")

        created_project = mock_repo.create_project.call_args[0][0]
        assert created_project.status_id == inactive_id

    @pytest.mark.asyncio
    async def test_sync_projects_sets_created_by(self, service, mock_repo, sample_project_request):
        """Should set created_by to the authenticated service account."""
        mock_repo.get_inactive_status.return_value = Status(
            status_id=uuid.uuid4(), status_name="Inactive", is_active=1
        )
        mock_repo.get_project_by_sn_project_id.return_value = None
        mock_repo.create_project.return_value = MagicMock()

        await service.sync_projects(sample_project_request, "servicenow@zeb.co")

        created_project = mock_repo.create_project.call_args[0][0]
        assert created_project.created_by == "servicenow@zeb.co"

    @pytest.mark.asyncio
    async def test_sync_projects_stores_specialization_name(self, service, mock_repo, sample_project_request):
        """Should store specialization_name on the project record."""
        mock_repo.get_inactive_status.return_value = Status(
            status_id=uuid.uuid4(), status_name="Inactive", is_active=1
        )
        mock_repo.get_project_by_sn_project_id.return_value = None
        mock_repo.create_project.return_value = MagicMock()

        await service.sync_projects(sample_project_request, "servicenow@zeb.co")

        created_project = mock_repo.create_project.call_args[0][0]
        assert created_project.specialization_name == "DevSecOps"


class TestSyncDevsecopsTickets:
    """Tests for sync_devsecops_tickets method."""

    @pytest.mark.asyncio
    async def test_sync_tickets_creates_ticket_and_repos(self, service, mock_repo, sample_ticket_request):
        """Should create ticket and repository records when none exist."""
        spec = Specialization(specialization_id=uuid.uuid4(), specialization_name="DevSecOps", is_active=1)
        project = Project(
            project_id=uuid.uuid4(),
            sn_project_id="SN-PRJ-001",
            project_name="Test Project",
            onboarded_date=date(2026, 1, 1),
            project_type="Infrastructure",
        )
        mock_repo.get_specialization_by_name.return_value = spec
        mock_repo.get_project_by_sn_project_id.return_value = project
        mock_repo.get_ticket_by_sn_or_devsec_id.return_value = None  # No existing ticket
        mock_repo.get_repository_by_ado_repo_id_and_ticket.return_value = None  # No existing repo
        mock_repo.create_ticket.return_value = MagicMock()
        mock_repo.create_repository.return_value = MagicMock()

        result = await service.sync_devsecops_tickets(sample_ticket_request, "servicenow@zeb.co")

        assert result["created"] == 1
        assert result["failed"] == 0
        mock_repo.create_ticket.assert_called_once()
        mock_repo.create_repository.assert_called_once()

    @pytest.mark.asyncio
    async def test_sync_tickets_skips_unknown_specialization(self, service, mock_repo, sample_ticket_request):
        """Should skip ticket when specialization is not found."""
        mock_repo.get_specialization_by_name.return_value = None

        result = await service.sync_devsecops_tickets(sample_ticket_request, "servicenow@zeb.co")

        assert result["created"] == 0
        assert result["failed"] == 1
        mock_repo.create_ticket.assert_not_called()

    @pytest.mark.asyncio
    async def test_sync_tickets_fallback_to_project_name(self, service, mock_repo, sample_ticket_request):
        """Should resolve project by name when sn_project_id doesn't match."""
        spec = Specialization(specialization_id=uuid.uuid4(), specialization_name="DevSecOps", is_active=1)
        project = Project(
            project_id=uuid.uuid4(),
            sn_project_id="SN-OTHER",
            project_name="Test Project",
            onboarded_date=date(2026, 1, 1),
            project_type="Infrastructure",
        )
        mock_repo.get_specialization_by_name.return_value = spec
        mock_repo.get_project_by_sn_project_id.return_value = None
        mock_repo.get_project_by_name.return_value = project
        mock_repo.get_ticket_by_sn_or_devsec_id.return_value = None
        mock_repo.get_repository_by_ado_repo_id_and_ticket.return_value = None
        mock_repo.create_ticket.return_value = MagicMock()
        mock_repo.create_repository.return_value = MagicMock()

        result = await service.sync_devsecops_tickets(sample_ticket_request, "servicenow@zeb.co")

        assert result["created"] == 1
        mock_repo.get_project_by_name.assert_called_once_with("Test Project")

    @pytest.mark.asyncio
    async def test_sync_tickets_fallback_to_client(self, service, mock_repo, sample_ticket_request):
        """Should resolve project by client when name doesn't match."""
        spec = Specialization(specialization_id=uuid.uuid4(), specialization_name="DevSecOps", is_active=1)
        project = Project(
            project_id=uuid.uuid4(),
            sn_project_id="SN-OTHER",
            project_name="Other",
            onboarded_date=date(2026, 1, 1),
            project_type="Infrastructure",
        )
        mock_repo.get_specialization_by_name.return_value = spec
        mock_repo.get_project_by_sn_project_id.return_value = None
        mock_repo.get_project_by_name.return_value = None
        mock_repo.get_project_by_client.return_value = project
        mock_repo.get_ticket_by_sn_or_devsec_id.return_value = None
        mock_repo.get_repository_by_ado_repo_id_and_ticket.return_value = None
        mock_repo.create_ticket.return_value = MagicMock()
        mock_repo.create_repository.return_value = MagicMock()

        result = await service.sync_devsecops_tickets(sample_ticket_request, "servicenow@zeb.co")

        assert result["created"] == 1
        mock_repo.get_project_by_client.assert_called_once_with("ABN AMRO")

    @pytest.mark.asyncio
    async def test_sync_tickets_fallback_to_default_project(self, service, mock_repo, sample_ticket_request):
        """Should use default project when all resolution steps fail."""
        spec = Specialization(specialization_id=uuid.uuid4(), specialization_name="DevSecOps", is_active=1)
        default_project = Project(
            project_id=uuid.uuid4(),
            sn_project_id="DEFAULT",
            project_name="Default",
            onboarded_date=date(2026, 1, 1),
            project_type="Default",
        )
        mock_repo.get_specialization_by_name.return_value = spec
        mock_repo.get_project_by_sn_project_id.return_value = None
        mock_repo.get_project_by_name.return_value = None
        mock_repo.get_project_by_client.return_value = None
        mock_repo.get_default_project.return_value = default_project
        mock_repo.get_ticket_by_sn_or_devsec_id.return_value = None
        mock_repo.get_repository_by_ado_repo_id_and_ticket.return_value = None
        mock_repo.create_ticket.return_value = MagicMock()
        mock_repo.create_repository.return_value = MagicMock()

        result = await service.sync_devsecops_tickets(sample_ticket_request, "servicenow@zeb.co")

        assert result["created"] == 1
        mock_repo.get_default_project.assert_called_once()

    @pytest.mark.asyncio
    async def test_sync_tickets_stores_lead_approvers(self, service, mock_repo, sample_ticket_request):
        """Should store lead_approvers as comma-separated string."""
        spec = Specialization(specialization_id=uuid.uuid4(), specialization_name="DevSecOps", is_active=1)
        project = Project(
            project_id=uuid.uuid4(),
            sn_project_id="SN-PRJ-001",
            project_name="Test Project",
            onboarded_date=date(2026, 1, 1),
            project_type="Infrastructure",
        )
        mock_repo.get_specialization_by_name.return_value = spec
        mock_repo.get_project_by_sn_project_id.return_value = project
        mock_repo.get_ticket_by_sn_or_devsec_id.return_value = None  # Create new ticket
        mock_repo.get_repository_by_ado_repo_id_and_ticket.return_value = None  # Create new repo
        mock_repo.create_ticket.return_value = MagicMock()
        mock_repo.create_repository.return_value = MagicMock()

        await service.sync_devsecops_tickets(sample_ticket_request, "servicenow@zeb.co")

        created_repo = mock_repo.create_repository.call_args[0][0]
        assert created_repo.lead_approvers == "lead1@zeb.co,lead2@zeb.co"

    @pytest.mark.asyncio
    async def test_sync_tickets_partial_success(self, service, mock_repo):
        """Should process valid tickets even when some fail."""
        request = SyncDevSecOpsTicketsRequest(
            tickets=[
                SyncDevSecOpsTicketItem(
                    sn_project_id="SN-001",
                    project_name="Project 1",
                    specialization_name="Unknown",  # Will fail
                ),
                SyncDevSecOpsTicketItem(
                    sn_project_id="SN-002",
                    project_name="Project 2",
                    specialization_name="DevSecOps",  # Will succeed
                ),
            ]
        )
        spec = Specialization(specialization_id=uuid.uuid4(), specialization_name="DevSecOps", is_active=1)
        project = Project(
            project_id=uuid.uuid4(),
            sn_project_id="SN-002",
            project_name="Project 2",
            onboarded_date=date(2026, 1, 1),
            project_type="Infrastructure",
        )

        # First ticket: specialization not found
        # Second ticket: specialization found
        mock_repo.get_specialization_by_name.side_effect = [None, spec]
        mock_repo.get_project_by_sn_project_id.return_value = project
        mock_repo.create_ticket.return_value = MagicMock()

        result = await service.sync_devsecops_tickets(request, "servicenow@zeb.co")

        assert result["created"] == 1
        assert result["failed"] == 1
        assert result["total"] == 2
