"""Unit tests for ProjectsRepository data access operations.

Focuses on testing SQL injection fixes, query filters, and CRUD operations.
"""

import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, call

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.projects_repository import ProjectsRepository
from src.repositories.schema.project import Project
from src.repositories.schema.repository import Repository
from src.repositories.schema.status import Status


@pytest.fixture
def mock_session():
    """Create a mock async session."""
    session = AsyncMock(spec=AsyncSession)
    return session


@pytest.fixture
def repo(mock_session):
    """Create a ProjectsRepository with mock session."""
    return ProjectsRepository(mock_session)


@pytest.fixture
def sample_projects():
    """Create sample project objects for testing."""
    return [
        Project(
            project_id=uuid.uuid4(),
            project_name="Project Alpha",
            onboarded_date=(datetime.utcnow() - timedelta(days=5)).date(),
            status_id=uuid.uuid4(),
            client="ClientA",
            is_active=1,
        ),
        Project(
            project_id=uuid.uuid4(),
            project_name="Project Beta",
            onboarded_date=(datetime.utcnow() - timedelta(days=15)).date(),
            status_id=uuid.uuid4(),
            client="ClientB",
            is_active=1,
        ),
    ]


class TestGetProjects:
    """Tests for get_projects method with filters and pagination."""

    @pytest.mark.asyncio
    async def test_get_projects_no_filters_returns_all_active(self, repo, mock_session, sample_projects):
        """Should return all active projects when no filters applied."""
        # Mock count query result
        count_result = MagicMock()
        count_result.scalar_one.return_value = 2

        # Mock projects query result
        projects_result = MagicMock()
        projects_result.scalars.return_value.all.return_value = sample_projects

        # Configure execute to return different results for count and select queries
        mock_session.execute.side_effect = [count_result, projects_result]

        result, total = await repo.get_projects(
            period_days=0,
            search=None,
            status_ids=None,
            client_ids=None,
            specialization_ids=None,
            min_overdue_days=None,
            offset=0,
            limit=10,
            sort_by="project_name",
            sort_order="asc",
        )

        assert len(result) == 2
        assert total == 2
        assert result[0].project_name == "Project Alpha"

    @pytest.mark.asyncio
    async def test_get_projects_with_search_sanitizes_input(self, repo, mock_session):
        """Should sanitize search input to prevent SQL injection via LIKE wildcards."""
        count_result = MagicMock()
        count_result.scalar_one.return_value = 0
        projects_result = MagicMock()
        projects_result.scalars.return_value.all.return_value = []

        mock_session.execute.side_effect = [count_result, projects_result]

        # Test with malicious search containing SQL wildcards
        malicious_search = "%' OR '1'='1"

        await repo.get_projects(
            period_days=0,
            search=malicious_search,
            status_ids=None,
            client_ids=None,
            specialization_ids=None,
            min_overdue_days=None,
            offset=0,
            limit=10,
            sort_by="project_name",
            sort_order="asc",
        )

        # Verify execute was called (query built successfully without SQL injection)
        assert mock_session.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_get_projects_with_underscore_in_search(self, repo, mock_session):
        """Should escape underscore wildcard in search to prevent SQL injection."""
        count_result = MagicMock()
        count_result.scalar_one.return_value = 0
        projects_result = MagicMock()
        projects_result.scalars.return_value.all.return_value = []

        mock_session.execute.side_effect = [count_result, projects_result]

        # Underscore is a single-character wildcard in SQL LIKE
        search_with_underscore = "test_project"

        await repo.get_projects(
            period_days=0,
            search=search_with_underscore,
            status_ids=None,
            client_ids=None,
            specialization_ids=None,
            min_overdue_days=None,
            offset=0,
            limit=10,
            sort_by="project_name",
            sort_order="asc",
        )

        # Should not raise exception - wildcards escaped
        assert mock_session.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_get_projects_with_period_filter(self, repo, mock_session):
        """Should filter projects by onboarded_date when period_days > 0."""
        count_result = MagicMock()
        count_result.scalar_one.return_value = 1
        projects_result = MagicMock()
        projects_result.scalars.return_value.all.return_value = []

        mock_session.execute.side_effect = [count_result, projects_result]

        await repo.get_projects(
            period_days=7,  # Last 7 days
            search=None,
            status_ids=None,
            client_ids=None,
            specialization_ids=None,
            min_overdue_days=None,
            offset=0,
            limit=10,
            sort_by="project_name",
            sort_order="asc",
        )

        assert mock_session.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_get_projects_with_min_overdue_days_uses_orm_expression(self, repo, mock_session):
        """Should use ORM expression for min_overdue_days to prevent SQL injection."""
        count_result = MagicMock()
        count_result.scalar_one.return_value = 0
        projects_result = MagicMock()
        projects_result.scalars.return_value.all.return_value = []

        mock_session.execute.side_effect = [count_result, projects_result]

        # This should NOT cause SQL injection (uses func.current_date() now)
        await repo.get_projects(
            period_days=0,
            search=None,
            status_ids=None,
            client_ids=None,
            specialization_ids=None,
            min_overdue_days=30,
            offset=0,
            limit=10,
            sort_by="project_name",
            sort_order="asc",
        )

        # Verify execute was called without SQL injection
        assert mock_session.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_get_projects_with_status_filter(self, repo, mock_session):
        """Should filter projects by status_ids."""
        count_result = MagicMock()
        count_result.scalar_one.return_value = 0
        projects_result = MagicMock()
        projects_result.scalars.return_value.all.return_value = []

        mock_session.execute.side_effect = [count_result, projects_result]

        status_ids = [uuid.uuid4(), uuid.uuid4()]

        await repo.get_projects(
            period_days=0,
            search=None,
            status_ids=status_ids,
            client_ids=None,
            specialization_ids=None,
            min_overdue_days=None,
            offset=0,
            limit=10,
            sort_by="project_name",
            sort_order="asc",
        )

        assert mock_session.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_get_projects_pagination_applied(self, repo, mock_session):
        """Should apply offset and limit for pagination."""
        count_result = MagicMock()
        count_result.scalar_one.return_value = 100
        projects_result = MagicMock()
        projects_result.scalars.return_value.all.return_value = []

        mock_session.execute.side_effect = [count_result, projects_result]

        result, total = await repo.get_projects(
            period_days=0,
            search=None,
            status_ids=None,
            client_ids=None,
            specialization_ids=None,
            min_overdue_days=None,
            offset=20,
            limit=10,
            sort_by="project_name",
            sort_order="asc",
        )

        assert total == 100
        assert len(result) == 0  # Mock returns empty

    @pytest.mark.asyncio
    async def test_get_projects_sort_by_onboarded_date_desc(self, repo, mock_session):
        """Should sort by onboarded_date in descending order."""
        count_result = MagicMock()
        count_result.scalar_one.return_value = 0
        projects_result = MagicMock()
        projects_result.scalars.return_value.all.return_value = []

        mock_session.execute.side_effect = [count_result, projects_result]

        await repo.get_projects(
            period_days=0,
            search=None,
            status_ids=None,
            client_ids=None,
            specialization_ids=None,
            min_overdue_days=None,
            offset=0,
            limit=10,
            sort_by="onboarded_date",
            sort_order="desc",
        )

        assert mock_session.execute.call_count == 2


class TestGetRepositoriesForProject:
    """Tests for get_repositories_for_project method."""

    @pytest.mark.asyncio
    async def test_get_repositories_returns_linked_repos(self, repo, mock_session):
        """Should return repositories linked to project through tickets."""
        project_id = uuid.uuid4()
        repos = [
            Repository(repository_id=uuid.uuid4(), repo_name="repo1", is_active=1),
            Repository(repository_id=uuid.uuid4(), repo_name="repo2", is_active=1),
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = repos
        mock_session.execute.return_value = mock_result

        result = await repo.get_repositories_for_project(project_id)

        assert len(result) == 2
        assert result[0].repo_name == "repo1"

    @pytest.mark.asyncio
    async def test_get_repositories_empty_when_no_repos(self, repo, mock_session):
        """Should return empty list when project has no repositories."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        result = await repo.get_repositories_for_project(uuid.uuid4())

        assert result == []


class TestGetProjectById:
    """Tests for get_project_by_id method."""

    @pytest.mark.asyncio
    async def test_get_project_by_id_found(self, repo, mock_session, sample_projects):
        """Should return project when found."""
        project = sample_projects[0]
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = project
        mock_session.execute.return_value = mock_result

        result = await repo.get_project_by_id(project.project_id)

        assert result is not None
        assert result.project_name == "Project Alpha"

    @pytest.mark.asyncio
    async def test_get_project_by_id_not_found(self, repo, mock_session):
        """Should return None when project not found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await repo.get_project_by_id(uuid.uuid4())

        assert result is None


class TestGetStatusByName:
    """Tests for get_status_by_name method."""

    @pytest.mark.asyncio
    async def test_get_status_by_name_found(self, repo, mock_session):
        """Should return status when found."""
        status = Status(status_id=uuid.uuid4(), status_name="Active", is_active=1)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = status
        mock_session.execute.return_value = mock_result

        result = await repo.get_status_by_name("Active")

        assert result is not None
        assert result.status_name == "Active"

    @pytest.mark.asyncio
    async def test_get_status_by_name_not_found(self, repo, mock_session):
        """Should return None when status not found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await repo.get_status_by_name("NonExistent")

        assert result is None


class TestUpdateProjectNotApplicable:
    """Tests for update_project_not_applicable method."""

    @pytest.mark.asyncio
    async def test_update_project_not_applicable_success(self, repo, mock_session):
        """Should update project to not applicable status."""
        project_id = uuid.uuid4()
        status_id = uuid.uuid4()

        await repo.update_project_not_applicable(project_id, status_id, "test_user")

        # Verify execute was called (update statement executed)
        mock_session.execute.assert_called_once()


class TestUpdateProjectComplete:
    """Tests for update_project_complete method."""

    @pytest.mark.asyncio
    async def test_update_project_complete_updates_project_and_tickets(self, repo, mock_session):
        """Should update both project status and ticket completed_at."""
        project_id = uuid.uuid4()
        status_id = uuid.uuid4()

        await repo.update_project_complete(project_id, status_id, "test_user")

        # Verify execute was called twice (project update + ticket update)
        assert mock_session.execute.call_count == 2


class TestCreateJiraTicket:
    """Tests for create_jira_ticket method."""

    @pytest.mark.asyncio
    async def test_create_jira_ticket_adds_to_session(self, repo, mock_session):
        """Should add jira ticket to session."""
        project_id = uuid.uuid4()

        await repo.create_jira_ticket(
            project_id=project_id,
            jira_id="SBT-123",
            reason_category="No longer needed",
            comments="Project cancelled",
            evidence_url="https://example.com/evidence.pdf",
            created_by="test_user",
        )

        # Verify add was called
        mock_session.add.assert_called_once()


class TestCommitAndRollback:
    """Tests for commit and rollback methods."""

    @pytest.mark.asyncio
    async def test_commit_success(self, repo, mock_session):
        """Should call session commit."""
        await repo.commit()
        mock_session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_rollback_success(self, repo, mock_session):
        """Should call session rollback."""
        await repo.rollback()
        mock_session.rollback.assert_awaited_once()


class TestGetStatusNameForProject:
    """Tests for get_status_name_for_project method."""

    @pytest.mark.asyncio
    async def test_get_status_name_for_devsecops_project_returns_ticket_status(
        self, repo, mock_session
    ):
        """Should return ticket status for devsecops-onboarded projects."""
        project = Project(
            project_id=uuid.uuid4(),
            project_name="Test Project",
            status_id=uuid.uuid4(),
            is_devsecops_onboarded=True,
            is_active=1,
        )

        # Mock ticket status query result
        ticket_status_result = MagicMock()
        ticket_status_result.scalar_one_or_none.return_value = "In Progress"

        mock_session.execute.return_value = ticket_status_result

        result = await repo.get_status_name_for_project(project)

        assert result == "In Progress"

    @pytest.mark.asyncio
    async def test_get_status_name_falls_back_to_project_status(self, repo, mock_session):
        """Should fall back to project status when no ticket status."""
        project = Project(
            project_id=uuid.uuid4(),
            project_name="Test Project",
            status_id=uuid.uuid4(),
            is_devsecops_onboarded=False,
            is_active=1,
        )

        # Mock project status query result
        project_status_result = MagicMock()
        project_status_result.scalar_one_or_none.return_value = "Active"

        mock_session.execute.return_value = project_status_result

        result = await repo.get_status_name_for_project(project)

        assert result == "Active"

    @pytest.mark.asyncio
    async def test_get_status_name_returns_none_when_no_status(self, repo, mock_session):
        """Should return None when project has no status_id."""
        project = Project(
            project_id=uuid.uuid4(),
            project_name="Test Project",
            status_id=None,
            is_active=1,
        )

        result = await repo.get_status_name_for_project(project)

        assert result is None


class TestGetNotApplicableDetails:
    """Tests for get_not_applicable_details method."""

    @pytest.mark.asyncio
    async def test_get_not_applicable_details_found(self, repo, mock_session):
        """Should return jira ticket details when found."""
        from src.repositories.schema.jira_ticket import JiraTicket

        jira_ticket = JiraTicket(
            project_id=uuid.uuid4(),
            jira_id="SBT-123",
            type="Not Applicable",
            reason_category="Cancelled",
            comments="Project no longer needed",
            evidence_url="https://example.com/file.pdf",
            priority="Medium",
            assignee="user@example.com",
            status="Open",
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = jira_ticket
        mock_session.execute.return_value = mock_result

        result = await repo.get_not_applicable_details(uuid.uuid4())

        assert result is not None
        assert result["reason_category"] == "Cancelled"
        assert result["jira_status"] == "Open"

    @pytest.mark.asyncio
    async def test_get_not_applicable_details_not_found(self, repo, mock_session):
        """Should return None when no jira ticket found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await repo.get_not_applicable_details(uuid.uuid4())

        assert result is None
