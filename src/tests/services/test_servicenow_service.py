"""Tests for ServiceNowService business logic."""

import uuid
from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.exc import SQLAlchemyError

from src.models.request.servicenow_request import (
    RepositoryItemRequest,
    SyncDevSecOpsTicketItemRequest,
    SyncDevSecOpsTicketsRequest,
    SyncProjectItemRequest,
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
            SyncProjectItemRequest(
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
            SyncDevSecOpsTicketItemRequest(
                sn_project_id="SN-PRJ-001",
                ado_project_name="Test Project",
                client="ABN AMRO",
                repositories=[
                    RepositoryItemRequest(
                        ado_repo_name="payments-api",
                        ado_repo_id="ado-001",
                        l1_approvers=["lead1@zeb.co", "lead2@zeb.co"],
                        specialization=["DevSecOps"],
                    )
                ],
                requested_by="requester@zeb.co",
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
    async def test_sync_projects_mixed_batch(self, service, mock_repo):
        """Should handle mix of new and existing projects."""
        existing_project = Project(
            project_id=uuid.uuid4(),
            sn_project_id="SN-001",
            project_name="Existing",
            onboarded_date=date(2026, 1, 1),
            project_type="App",
        )
        mock_repo.get_inactive_status.return_value = Status(
            status_id=uuid.uuid4(), status_name="Inactive", is_active=1
        )
        # First project exists, second is new
        mock_repo.get_project_by_sn_project_id.side_effect = [existing_project, None]
        mock_repo.update_project.return_value = existing_project
        mock_repo.create_project.return_value = MagicMock()

        request = SyncProjectRequest(
            projects=[
                SyncProjectItemRequest(
                    sn_project_id="SN-001",
                    project_name="Existing Updated",
                    onboarded_date=date(2026, 1, 1),
                    project_type="App",
                ),
                SyncProjectItemRequest(
                    sn_project_id="SN-002",
                    project_name="Brand New",
                    onboarded_date=date(2026, 5, 1),
                    project_type="Platform",
                ),
            ]
        )

        result = await service.sync_projects(request, "servicenow@zeb.co")

        assert result["created"] == 1
        assert result["updated"] == 1
        assert result["total"] == 2

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
    async def test_sync_projects_no_inactive_status(self, service, mock_repo):
        """Should handle case where Inactive status doesn't exist (status_id=None)."""
        mock_repo.get_inactive_status.return_value = None
        mock_repo.get_project_by_sn_project_id.return_value = None
        mock_repo.create_project.return_value = MagicMock()

        request = SyncProjectRequest(
            projects=[
                SyncProjectItemRequest(
                    sn_project_id="SN-001",
                    project_name="Test",
                    onboarded_date=date(2026, 1, 1),
                    project_type="App",
                )
            ]
        )

        result = await service.sync_projects(request, "servicenow@zeb.co")

        assert result["created"] == 1
        created_project = mock_repo.create_project.call_args[0][0]
        assert created_project.status_id is None


class TestSyncDevsecopsTickets:
    """Tests for sync_devsecops_tickets method."""

    @pytest.mark.asyncio
    async def test_sync_tickets_creates_ticket_with_repos(self, service, mock_repo, sample_ticket_request):
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
        mock_repo.get_ticket_by_sn_or_devsec_id.return_value = None
        mock_repo.get_repository_by_ado_repo_id_and_ticket.return_value = None
        mock_repo.create_ticket.return_value = MagicMock()
        mock_repo.create_repository.return_value = MagicMock()

        result = await service.sync_devsecops_tickets(sample_ticket_request, "servicenow@zeb.co")

        assert result["created"] == 1
        assert result["failed"] == 0
        mock_repo.create_ticket.assert_called_once()
        mock_repo.create_repository.assert_called_once()

    @pytest.mark.asyncio
    async def test_sync_tickets_normalized_name_match(self, service, mock_repo):
        """Should resolve project by normalized name when exact match fails."""
        spec = Specialization(specialization_id=uuid.uuid4(), specialization_name="DevSecOps", is_active=1)
        project = Project(
            project_id=uuid.uuid4(),
            sn_project_id="SN-OTHER",
            project_name="Touchpoint PJ",
            onboarded_date=date(2026, 1, 1),
            project_type="Application",
        )
        request = SyncDevSecOpsTicketsRequest(
            tickets=[
                SyncDevSecOpsTicketItemRequest(
                    sn_project_id="SN-NEW",
                    ado_project_name="zeb-touchpoint-pj",
                    repositories=[
                        RepositoryItemRequest(
                            ado_repo_name="repo1",
                            specialization=["DevSecOps"],
                        )
                    ],
                )
            ]
        )
        mock_repo.get_specialization_by_name.return_value = spec
        mock_repo.get_project_by_sn_project_id.return_value = None
        mock_repo.get_project_by_name.return_value = None
        mock_repo.get_project_by_normalized_name.return_value = project
        mock_repo.get_ticket_by_sn_or_devsec_id.return_value = None
        mock_repo.create_ticket.return_value = MagicMock()

        result = await service.sync_devsecops_tickets(request, "servicenow@zeb.co")

        assert result["created"] == 1
        mock_repo.get_project_by_normalized_name.assert_called_once_with("zeb-touchpoint-pj")

    @pytest.mark.asyncio
    async def test_sync_tickets_marks_project_onboarded(self, service, mock_repo):
        """Should call mark_project_onboarded on the resolved project."""
        spec = Specialization(specialization_id=uuid.uuid4(), specialization_name="DevSecOps", is_active=1)
        project = Project(
            project_id=uuid.uuid4(),
            sn_project_id="SN-PRJ-001",
            project_name="Test Project",
            onboarded_date=date(2026, 1, 1),
            project_type="Application",
            is_devsecops_onboarded=False,
        )
        request = SyncDevSecOpsTicketsRequest(
            tickets=[
                SyncDevSecOpsTicketItemRequest(
                    sn_project_id="SN-PRJ-001",
                    ado_project_name="Test Project",
                    repositories=[
                        RepositoryItemRequest(
                            ado_repo_name="repo1",
                            specialization=["DevSecOps"],
                        )
                    ],
                )
            ]
        )
        mock_repo.get_specialization_by_name.return_value = spec
        mock_repo.get_project_by_sn_project_id.return_value = project
        mock_repo.get_ticket_by_sn_or_devsec_id.return_value = None
        mock_repo.create_ticket.return_value = MagicMock()

        await service.sync_devsecops_tickets(request, "servicenow@zeb.co")

        mock_repo.mark_project_onboarded.assert_called_once_with(project, "servicenow@zeb.co")

    @pytest.mark.asyncio
    async def test_sync_tickets_partial_success(self, service, mock_repo):
        """Should process valid tickets even when some fail."""
        request = SyncDevSecOpsTicketsRequest(
            tickets=[
                SyncDevSecOpsTicketItemRequest(
                    sn_project_id="SN-001",
                    ado_project_name="Project 1",
                    repositories=[RepositoryItemRequest(ado_repo_name="repo1", specialization=["Unknown"])],
                ),
                SyncDevSecOpsTicketItemRequest(
                    sn_project_id="SN-002",
                    ado_project_name="Project 2",
                    repositories=[RepositoryItemRequest(ado_repo_name="repo2", specialization=["DevSecOps"])],
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

        # First ticket: specialization not found; Second ticket: found
        mock_repo.get_specialization_by_name.side_effect = [None, spec]
        mock_repo.get_project_by_sn_project_id.return_value = project
        mock_repo.get_ticket_by_sn_or_devsec_id.return_value = None
        mock_repo.create_ticket.return_value = MagicMock()

        result = await service.sync_devsecops_tickets(request, "servicenow@zeb.co")

        assert result["created"] == 1
        assert result["failed"] == 1
        assert result["total"] == 2

    @pytest.mark.asyncio
    async def test_sync_tickets_unknown_specialization_skipped(self, service, mock_repo, sample_ticket_request):
        """Should skip ticket when specialization is not found."""
        mock_repo.get_specialization_by_name.return_value = None

        result = await service.sync_devsecops_tickets(sample_ticket_request, "servicenow@zeb.co")

        assert result["created"] == 0
        assert result["failed"] == 1
        mock_repo.create_ticket.assert_not_called()

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
        mock_repo.get_ticket_by_sn_or_devsec_id.return_value = None
        mock_repo.get_repository_by_ado_repo_id_and_ticket.return_value = None
        mock_repo.create_ticket.return_value = MagicMock()
        mock_repo.create_repository.return_value = MagicMock()

        await service.sync_devsecops_tickets(sample_ticket_request, "servicenow@zeb.co")

        created_repo = mock_repo.create_repository.call_args[0][0]
        assert created_repo.lead_approvers == "lead1@zeb.co,lead2@zeb.co"

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
        mock_repo.get_project_by_normalized_name.return_value = None
        mock_repo.get_project_by_client.return_value = project
        mock_repo.get_ticket_by_sn_or_devsec_id.return_value = None
        mock_repo.get_repository_by_ado_repo_id_and_ticket.return_value = None
        mock_repo.create_ticket.return_value = MagicMock()
        mock_repo.create_repository.return_value = MagicMock()

        result = await service.sync_devsecops_tickets(sample_ticket_request, "servicenow@zeb.co")

        assert result["created"] == 1
        mock_repo.get_project_by_client.assert_called_once_with("ABN AMRO")

    @pytest.mark.asyncio
    async def test_sync_tickets_no_project_found_skips(self, service, mock_repo):
        """Should auto-create project when no project can be resolved."""
        spec = Specialization(specialization_id=uuid.uuid4(), specialization_name="DevSecOps", is_active=1)
        request = SyncDevSecOpsTicketsRequest(
            tickets=[
                SyncDevSecOpsTicketItemRequest(
                    sn_project_id="SN-UNKNOWN",
                    ado_project_name="Unknown Project",
                    repositories=[RepositoryItemRequest(ado_repo_name="repo1", specialization=["DevSecOps"])],
                )
            ]
        )
        inactive_status = MagicMock()
        inactive_status.status_id = uuid.uuid4()
        mock_repo.get_specialization_by_name.return_value = spec
        mock_repo.get_project_by_sn_project_id.return_value = None
        mock_repo.get_project_by_name.return_value = None
        mock_repo.get_project_by_normalized_name.return_value = None
        mock_repo.get_project_by_client.return_value = None
        mock_repo.get_inactive_status.return_value = inactive_status
        mock_repo.create_project.return_value = MagicMock()
        mock_repo.get_ticket_by_sn_or_devsec_id.return_value = None
        mock_repo.get_repository_by_ado_repo_id_and_ticket.return_value = None
        mock_repo.create_ticket.return_value = MagicMock()
        mock_repo.create_repository.return_value = MagicMock()

        result = await service.sync_devsecops_tickets(request, "servicenow@zeb.co")

        # Service auto-creates project when none found
        assert result["created"] == 1
        mock_repo.create_project.assert_called_once()

    @pytest.mark.asyncio
    async def test_sync_tickets_exception_counts_as_failed(self, service, mock_repo):
        """Should count tickets that throw exceptions as failed."""
        spec = Specialization(specialization_id=uuid.uuid4(), specialization_name="DevSecOps", is_active=1)
        project = Project(
            project_id=uuid.uuid4(),
            sn_project_id="SN-PRJ-001",
            project_name="Test",
            onboarded_date=date(2026, 1, 1),
            project_type="App",
            is_devsecops_onboarded=True,
        )
        request = SyncDevSecOpsTicketsRequest(
            tickets=[
                SyncDevSecOpsTicketItemRequest(
                    sn_project_id="SN-PRJ-001",
                    ado_project_name="Test",
                    repositories=[RepositoryItemRequest(ado_repo_name="repo1", specialization=["DevSecOps"])],
                )
            ]
        )
        mock_repo.get_specialization_by_name.return_value = spec
        mock_repo.get_project_by_sn_project_id.return_value = project
        mock_repo.get_ticket_by_sn_or_devsec_id.side_effect = SQLAlchemyError("DB error")

        result = await service.sync_devsecops_tickets(request, "servicenow@zeb.co")

        assert result["created"] == 0
        assert result["failed"] == 1

    @pytest.mark.asyncio
    async def test_sync_tickets_updates_existing_ticket(self, service, mock_repo):
        """Should update an existing ticket instead of creating a new one."""
        spec = Specialization(specialization_id=uuid.uuid4(), specialization_name="DevSecOps", is_active=1)
        project = Project(
            project_id=uuid.uuid4(),
            sn_project_id="SN-PRJ-001",
            project_name="Test Project",
            onboarded_date=date(2026, 1, 1),
            project_type="Application",
            is_devsecops_onboarded=True,
        )
        existing_ticket = MagicMock()
        existing_ticket.ticket_id = uuid.uuid4()

        request = SyncDevSecOpsTicketsRequest(
            tickets=[
                SyncDevSecOpsTicketItemRequest(
                    sn_project_id="SN-PRJ-001",
                    ado_project_name="Test Project",
                    repositories=[RepositoryItemRequest(ado_repo_name="repo1", specialization=["DevSecOps"])],
                    requested_by="new-requester@zeb.co",
                )
            ]
        )
        mock_repo.get_specialization_by_name.return_value = spec
        mock_repo.get_project_by_sn_project_id.return_value = project
        mock_repo.get_ticket_by_sn_or_devsec_id.return_value = existing_ticket

        result = await service.sync_devsecops_tickets(request, "servicenow@zeb.co")

        assert result["created"] == 1
        mock_repo.update_ticket.assert_called_once()
        mock_repo.create_ticket.assert_not_called()

    @pytest.mark.asyncio
    async def test_sync_tickets_fallback_to_default_project(self, service, mock_repo, sample_ticket_request):
        """Should auto-create project when all resolution steps fail."""
        spec = Specialization(specialization_id=uuid.uuid4(), specialization_name="DevSecOps", is_active=1)
        inactive_status = MagicMock()
        inactive_status.status_id = uuid.uuid4()
        mock_repo.get_specialization_by_name.return_value = spec
        mock_repo.get_project_by_sn_project_id.return_value = None
        mock_repo.get_project_by_name.return_value = None
        mock_repo.get_project_by_normalized_name.return_value = None
        mock_repo.get_project_by_client.return_value = None
        mock_repo.get_inactive_status.return_value = inactive_status
        mock_repo.create_project.return_value = MagicMock()
        mock_repo.get_ticket_by_sn_or_devsec_id.return_value = None
        mock_repo.get_repository_by_ado_repo_id_and_ticket.return_value = None
        mock_repo.create_ticket.return_value = MagicMock()
        mock_repo.create_repository.return_value = MagicMock()

        result = await service.sync_devsecops_tickets(sample_ticket_request, "servicenow@zeb.co")

        assert result["created"] == 1
        mock_repo.create_project.assert_called_once()
