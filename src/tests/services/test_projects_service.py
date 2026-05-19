"""Unit tests for ProjectsService.

Tests cover both GET /api/v1/projects (get_projects) and
POST /api/v1/projects/action (perform_action) with positive and negative scenarios.

Validates: ZDAD-48-FR01 through ZDAD-48-FR05
"""

import uuid
from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.client.s3_client import S3Client
from src.repositories.projects_repository import ProjectsRepository
from src.services.projects_service import ProjectsService
from src.utils.exceptions import InvalidParameterError, NotFoundError


@pytest.fixture
def mock_projects_repo():
    """Create a mock ProjectsRepository."""
    return AsyncMock(spec=ProjectsRepository)


@pytest.fixture
def mock_s3_client():
    """Create a mock S3Client."""
    return AsyncMock(spec=S3Client)


@pytest.fixture
def service(mock_projects_repo, mock_s3_client):
    """Create a ProjectsService with mocked dependencies."""
    return ProjectsService(
        projects_repo=mock_projects_repo,
        s3_client=mock_s3_client,
    )


def _make_project(**kwargs):
    """Helper to create a mock Project ORM object."""
    project = MagicMock()
    project.project_id = kwargs.get("project_id", uuid.uuid4())
    project.project_name = kwargs.get("project_name", "Test Project")
    project.onboarded_date = kwargs.get("onboarded_date", date(2026, 1, 15))
    project.status_id = kwargs.get("status_id", uuid.uuid4())
    project.is_applicable = kwargs.get("is_applicable", True)
    project.client = kwargs.get("client", "TestClient")
    return project


def _make_repository(**kwargs):
    """Helper to create a mock Repository ORM object."""
    repo = MagicMock()
    repo.repository_id = kwargs.get("repository_id", uuid.uuid4())
    repo.repository_name = kwargs.get("repository_name", "test-repo")
    repo.created_at = kwargs.get("created_at", datetime(2026, 2, 1))
    repo.pipeline_runs_count = kwargs.get("pipeline_runs_count", 5)
    repo.success_rate = kwargs.get("success_rate", 100.0)
    return repo


def _make_status(**kwargs):
    """Helper to create a mock Status ORM object."""
    status = MagicMock()
    status.status_id = kwargs.get("status_id", uuid.uuid4())
    status.status_name = kwargs.get("status_name", "Active")
    return status


class TestValidatePeriod:
    """Tests for ProjectsService._validate_period."""

    def test_none_defaults_to_last_month(self, service):
        """When period is None, defaults to 'last_month'."""
        result = service._validate_period(None)
        assert result == "last_month"

    def test_valid_last_week(self, service):
        """Accepts 'last_week' as valid."""
        assert service._validate_period("last_week") == "last_week"

    def test_valid_last_month(self, service):
        """Accepts 'last_month' as valid."""
        assert service._validate_period("last_month") == "last_month"

    def test_valid_last_3_months(self, service):
        """Accepts 'last_3_months' as valid."""
        assert service._validate_period("last_3_months") == "last_3_months"

    def test_valid_last_6_months(self, service):
        """Accepts 'last_6_months' as valid."""
        assert service._validate_period("last_6_months") == "last_6_months"

    def test_valid_last_year(self, service):
        """Accepts 'last_year' as valid."""
        assert service._validate_period("last_year") == "last_year"

    def test_invalid_period_raises_error(self, service):
        """Invalid period raises InvalidParameterError."""
        with pytest.raises(InvalidParameterError) as exc_info:
            service._validate_period("last_decade")
        assert "period" in exc_info.value.message

    def test_case_sensitive(self, service):
        """Period validation is case-sensitive."""
        with pytest.raises(InvalidParameterError):
            service._validate_period("Last_Month")


class TestValidateSortBy:
    """Tests for ProjectsService._validate_sort_by."""

    def test_none_defaults_to_project(self, service):
        """When sort_by is None, defaults to 'project'."""
        assert service._validate_sort_by(None) == "project"

    def test_valid_project(self, service):
        """Accepts 'project' as valid."""
        assert service._validate_sort_by("project") == "project"

    def test_valid_onboarded_date(self, service):
        """Accepts 'onboarded_date' as valid."""
        assert service._validate_sort_by("onboarded_date") == "onboarded_date"

    def test_invalid_sort_by_raises_error(self, service):
        """Invalid sort_by raises InvalidParameterError."""
        with pytest.raises(InvalidParameterError) as exc_info:
            service._validate_sort_by("status")
        assert "sort_by" in exc_info.value.message


class TestValidateSortOrder:
    """Tests for ProjectsService._validate_sort_order."""

    def test_none_defaults_to_asc(self, service):
        """When sort_order is None, defaults to 'asc'."""
        assert service._validate_sort_order(None) == "asc"

    def test_valid_asc(self, service):
        """Accepts 'asc' as valid."""
        assert service._validate_sort_order("asc") == "asc"

    def test_valid_desc(self, service):
        """Accepts 'desc' as valid."""
        assert service._validate_sort_order("desc") == "desc"

    def test_invalid_sort_order_raises_error(self, service):
        """Invalid sort_order raises InvalidParameterError."""
        with pytest.raises(InvalidParameterError) as exc_info:
            service._validate_sort_order("ascending")
        assert "sort_order" in exc_info.value.message


class TestValidateOffset:
    """Tests for ProjectsService._validate_offset."""

    def test_zero_is_valid(self, service):
        """Offset of 0 is valid."""
        service._validate_offset(0)  # Should not raise

    def test_positive_is_valid(self, service):
        """Positive offset is valid."""
        service._validate_offset(100)  # Should not raise

    def test_negative_raises_error(self, service):
        """Negative offset raises InvalidParameterError."""
        with pytest.raises(InvalidParameterError) as exc_info:
            service._validate_offset(-1)
        assert "offset" in exc_info.value.message


class TestValidateLimit:
    """Tests for ProjectsService._validate_limit."""

    def test_one_is_valid(self, service):
        """Limit of 1 is valid."""
        service._validate_limit(1)  # Should not raise

    def test_hundred_is_valid(self, service):
        """Limit of 100 is valid."""
        service._validate_limit(100)  # Should not raise

    def test_zero_raises_error(self, service):
        """Limit of 0 raises InvalidParameterError."""
        with pytest.raises(InvalidParameterError) as exc_info:
            service._validate_limit(0)
        assert "limit" in exc_info.value.message

    def test_over_hundred_raises_error(self, service):
        """Limit over 100 raises InvalidParameterError."""
        with pytest.raises(InvalidParameterError) as exc_info:
            service._validate_limit(101)
        assert "limit" in exc_info.value.message

    def test_negative_raises_error(self, service):
        """Negative limit raises InvalidParameterError."""
        with pytest.raises(InvalidParameterError):
            service._validate_limit(-5)


class TestValidateProjectId:
    """Tests for ProjectsService._validate_project_id."""

    def test_valid_uuid_string(self, service):
        """Valid UUID string is parsed correctly."""
        test_id = str(uuid.uuid4())
        result = service._validate_project_id(test_id)
        assert result == uuid.UUID(test_id)

    def test_empty_string_raises_error(self, service):
        """Empty string raises InvalidParameterError."""
        with pytest.raises(InvalidParameterError) as exc_info:
            service._validate_project_id("")
        assert "project_id" in exc_info.value.message

    def test_invalid_uuid_raises_error(self, service):
        """Invalid UUID format raises InvalidParameterError."""
        with pytest.raises(InvalidParameterError) as exc_info:
            service._validate_project_id("not-a-uuid")
        assert "project_id" in exc_info.value.message


class TestValidateAction:
    """Tests for ProjectsService._validate_action."""

    def test_mark_not_applicable_is_valid(self, service):
        """'mark_not_applicable' is a valid action."""
        service._validate_action("mark_not_applicable")  # Should not raise

    def test_mark_complete_is_valid(self, service):
        """'mark_complete' is a valid action."""
        service._validate_action("mark_complete")  # Should not raise

    def test_empty_string_raises_error(self, service):
        """Empty action raises InvalidParameterError."""
        with pytest.raises(InvalidParameterError) as exc_info:
            service._validate_action("")
        assert "action" in exc_info.value.message

    def test_invalid_action_raises_error(self, service):
        """Invalid action value raises InvalidParameterError."""
        with pytest.raises(InvalidParameterError) as exc_info:
            service._validate_action("delete")
        assert "action" in exc_info.value.message


class TestParseUuidCsv:
    """Tests for ProjectsService._parse_uuid_csv."""

    def test_none_returns_none(self, service):
        """None returns None."""
        assert service._parse_uuid_csv(None) is None

    def test_empty_string_returns_none(self, service):
        """Empty string returns None."""
        assert service._parse_uuid_csv("") is None

    def test_whitespace_returns_none(self, service):
        """Whitespace-only returns None."""
        assert service._parse_uuid_csv("   ") is None

    def test_single_valid_uuid(self, service):
        """Single valid UUID is parsed."""
        test_id = str(uuid.uuid4())
        result = service._parse_uuid_csv(test_id)
        assert result == [uuid.UUID(test_id)]

    def test_multiple_valid_uuids(self, service):
        """Multiple valid UUIDs are parsed."""
        id1, id2 = str(uuid.uuid4()), str(uuid.uuid4())
        result = service._parse_uuid_csv(f"{id1},{id2}")
        assert len(result) == 2

    def test_invalid_uuids_skipped(self, service):
        """Invalid UUIDs are skipped."""
        valid_id = str(uuid.uuid4())
        result = service._parse_uuid_csv(f"{valid_id},invalid,also-bad")
        assert result == [uuid.UUID(valid_id)]

    def test_all_invalid_returns_none(self, service):
        """All invalid UUIDs returns None."""
        assert service._parse_uuid_csv("bad,worse") is None


class TestParseCsv:
    """Tests for ProjectsService._parse_csv."""

    def test_none_returns_none(self, service):
        """None returns None."""
        assert service._parse_csv(None) is None

    def test_empty_string_returns_none(self, service):
        """Empty string returns None."""
        assert service._parse_csv("") is None

    def test_single_value(self, service):
        """Single value is parsed."""
        result = service._parse_csv("client_a")
        assert result == ["client_a"]

    def test_multiple_values(self, service):
        """Multiple values are parsed and trimmed."""
        result = service._parse_csv("client_a, client_b , client_c")
        assert result == ["client_a", "client_b", "client_c"]


class TestDetermineRepoStatus:
    """Tests for ProjectsService._determine_repo_status."""

    def test_passed_when_success_rate_positive(self, service):
        """PASSED when pipeline_runs_count > 0 and success_rate > 0."""
        repo = _make_repository(pipeline_runs_count=5, success_rate=80.0)
        assert service._determine_repo_status(repo) == "PASSED"

    def test_failed_when_success_rate_zero(self, service):
        """FAILED when pipeline_runs_count > 0 but success_rate is 0."""
        repo = _make_repository(pipeline_runs_count=3, success_rate=0)
        assert service._determine_repo_status(repo) == "FAILED"

    def test_passed_when_no_pipeline_runs(self, service):
        """PASSED when no pipeline runs exist (default state)."""
        repo = _make_repository(pipeline_runs_count=0, success_rate=0)
        assert service._determine_repo_status(repo) == "PASSED"

    def test_passed_when_pipeline_runs_none(self, service):
        """PASSED when pipeline_runs_count is None."""
        repo = _make_repository(pipeline_runs_count=None, success_rate=None)
        assert service._determine_repo_status(repo) == "PASSED"


class TestGetProjects:
    """Tests for ProjectsService.get_projects (integration with mocked repo)."""

    @pytest.mark.asyncio
    async def test_success_with_defaults(self, service, mock_projects_repo):
        """Successful retrieval with all default parameters."""
        project = _make_project()
        mock_projects_repo.get_projects.return_value = ([project], 1)
        mock_projects_repo.get_repositories_for_project.return_value = []
        mock_projects_repo.get_status_name_for_project.return_value = "Active"

        result = await service.get_projects(
            period=None, search=None, status=None, client=None,
            specialization=None, offset=0, limit=10, sort_by=None, sort_order=None,
        )

        assert result.status_code == 200
        assert result.status == "success"
        assert result.data["pagination"]["total_items"] == 1
        assert len(result.data["projects"]) == 1

    @pytest.mark.asyncio
    async def test_success_with_repositories(self, service, mock_projects_repo):
        """Projects include nested repositories."""
        project = _make_project()
        repo = _make_repository(repository_name="my-repo", pipeline_runs_count=2, success_rate=100.0)
        mock_projects_repo.get_projects.return_value = ([project], 1)
        mock_projects_repo.get_repositories_for_project.return_value = [repo]
        mock_projects_repo.get_status_name_for_project.return_value = "Active"

        result = await service.get_projects(
            period=None, search=None, status=None, client=None,
            specialization=None, offset=0, limit=10, sort_by=None, sort_order=None,
        )

        project_data = result.data["projects"][0]
        assert project_data["repository_count"] == 1
        assert project_data["repositories"][0]["name"] == "my-repo"
        assert project_data["repositories"][0]["status"] == "PASSED"

    @pytest.mark.asyncio
    async def test_empty_results(self, service, mock_projects_repo):
        """Empty project list returns empty array with zero total."""
        mock_projects_repo.get_projects.return_value = ([], 0)

        result = await service.get_projects(
            period=None, search=None, status=None, client=None,
            specialization=None, offset=0, limit=10, sort_by=None, sort_order=None,
        )

        assert result.data["projects"] == []
        assert result.data["pagination"]["total_items"] == 0

    @pytest.mark.asyncio
    async def test_invalid_period_raises_error(self, service):
        """Invalid period raises InvalidParameterError."""
        with pytest.raises(InvalidParameterError):
            await service.get_projects(
                period="invalid", search=None, status=None, client=None,
                specialization=None, offset=0, limit=10, sort_by=None, sort_order=None,
            )

    @pytest.mark.asyncio
    async def test_invalid_sort_by_raises_error(self, service):
        """Invalid sort_by raises InvalidParameterError."""
        with pytest.raises(InvalidParameterError):
            await service.get_projects(
                period=None, search=None, status=None, client=None,
                specialization=None, offset=0, limit=10, sort_by="invalid", sort_order=None,
            )

    @pytest.mark.asyncio
    async def test_invalid_sort_order_raises_error(self, service):
        """Invalid sort_order raises InvalidParameterError."""
        with pytest.raises(InvalidParameterError):
            await service.get_projects(
                period=None, search=None, status=None, client=None,
                specialization=None, offset=0, limit=10, sort_by=None, sort_order="random",
            )

    @pytest.mark.asyncio
    async def test_negative_offset_raises_error(self, service):
        """Negative offset raises InvalidParameterError."""
        with pytest.raises(InvalidParameterError):
            await service.get_projects(
                period=None, search=None, status=None, client=None,
                specialization=None, offset=-1, limit=10, sort_by=None, sort_order=None,
            )

    @pytest.mark.asyncio
    async def test_limit_over_100_raises_error(self, service):
        """Limit over 100 raises InvalidParameterError."""
        with pytest.raises(InvalidParameterError):
            await service.get_projects(
                period=None, search=None, status=None, client=None,
                specialization=None, offset=0, limit=200, sort_by=None, sort_order=None,
            )

    @pytest.mark.asyncio
    async def test_pagination_metadata_correct(self, service, mock_projects_repo):
        """Pagination metadata reflects offset, limit, and total."""
        mock_projects_repo.get_projects.return_value = ([], 44)

        result = await service.get_projects(
            period=None, search=None, status=None, client=None,
            specialization=None, offset=10, limit=5, sort_by=None, sort_order=None,
        )

        pagination = result.data["pagination"]
        assert pagination["offset"] == 10
        assert pagination["limit"] == 5
        assert pagination["total_items"] == 44

    @pytest.mark.asyncio
    async def test_filters_passed_to_repository(self, service, mock_projects_repo):
        """Filters are correctly passed to the repository layer."""
        status_id = str(uuid.uuid4())
        spec_id = str(uuid.uuid4())
        mock_projects_repo.get_projects.return_value = ([], 0)

        await service.get_projects(
            period="last_week", search="xenon", status=status_id,
            client="ClientA", specialization=spec_id,
            offset=5, limit=20, sort_by="onboarded_date", sort_order="desc",
        )

        call_kwargs = mock_projects_repo.get_projects.call_args[1]
        assert call_kwargs["period_days"] == 7
        assert call_kwargs["search"] == "xenon"
        assert call_kwargs["status_ids"] == [uuid.UUID(status_id)]
        assert call_kwargs["client_ids"] == ["ClientA"]
        assert call_kwargs["specialization_ids"] == [uuid.UUID(spec_id)]
        assert call_kwargs["offset"] == 5
        assert call_kwargs["limit"] == 20
        assert call_kwargs["sort_by"] == "onboarded_date"
        assert call_kwargs["sort_order"] == "desc"


class TestPerformActionMarkNotApplicable:
    """Tests for perform_action with mark_not_applicable."""

    @pytest.mark.asyncio
    async def test_success(self, service, mock_projects_repo, mock_s3_client):
        """Successful mark_not_applicable updates project and creates Jira ticket."""
        project_id = str(uuid.uuid4())
        project = _make_project(project_id=uuid.UUID(project_id))
        status = _make_status(status_name="Not Applicable")

        mock_projects_repo.get_project_by_id.return_value = project
        mock_projects_repo.get_status_by_name.return_value = status
        mock_projects_repo.update_project_not_applicable.return_value = None
        mock_projects_repo.create_jira_ticket.return_value = None
        mock_projects_repo.commit.return_value = None

        result = await service.perform_action(
            project_id=project_id,
            action="mark_not_applicable",
            reason_category="Out of scope",
            comments="Project does not require DevSecOps",
            evidence_file=None,
            user_id="test_user",
        )

        assert result.status_code == 200
        assert result.message == "Action performed successfully"
        mock_projects_repo.update_project_not_applicable.assert_called_once()
        mock_projects_repo.create_jira_ticket.assert_called_once()
        mock_projects_repo.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_missing_reason_category_raises_error(self, service, mock_projects_repo):
        """Missing reason_category raises InvalidParameterError."""
        project_id = str(uuid.uuid4())
        project = _make_project(project_id=uuid.UUID(project_id))
        status = _make_status(status_name="Not Applicable")

        mock_projects_repo.get_project_by_id.return_value = project
        mock_projects_repo.get_status_by_name.return_value = status

        with pytest.raises(InvalidParameterError) as exc_info:
            await service.perform_action(
                project_id=project_id,
                action="mark_not_applicable",
                reason_category=None,
                comments="Some comments",
                evidence_file=None,
                user_id="test_user",
            )
        assert "reason_category" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_missing_comments_raises_error(self, service, mock_projects_repo):
        """Missing comments raises InvalidParameterError."""
        project_id = str(uuid.uuid4())
        project = _make_project(project_id=uuid.UUID(project_id))
        status = _make_status(status_name="Not Applicable")

        mock_projects_repo.get_project_by_id.return_value = project
        mock_projects_repo.get_status_by_name.return_value = status

        with pytest.raises(InvalidParameterError) as exc_info:
            await service.perform_action(
                project_id=project_id,
                action="mark_not_applicable",
                reason_category="Out of scope",
                comments=None,
                evidence_file=None,
                user_id="test_user",
            )
        assert "comments" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_with_evidence_file(self, service, mock_projects_repo, mock_s3_client):
        """Evidence file is uploaded and URL stored in Jira ticket."""
        project_id = str(uuid.uuid4())
        project = _make_project(project_id=uuid.UUID(project_id))
        status = _make_status(status_name="Not Applicable")

        mock_projects_repo.get_project_by_id.return_value = project
        mock_projects_repo.get_status_by_name.return_value = status
        mock_projects_repo.update_project_not_applicable.return_value = None
        mock_projects_repo.create_jira_ticket.return_value = None
        mock_projects_repo.commit.return_value = None

        mock_file = AsyncMock()
        mock_file.filename = "evidence.pdf"
        mock_file.read.return_value = b"file content"
        mock_s3_client.upload_pdf.return_value = "s3://bucket/key"
        mock_s3_client.generate_presigned_url.return_value = "https://s3.example.com/evidence.pdf"

        result = await service.perform_action(
            project_id=project_id,
            action="mark_not_applicable",
            reason_category="Out of scope",
            comments="See attached evidence",
            evidence_file=mock_file,
            user_id="test_user",
        )

        assert result.status_code == 200
        mock_s3_client.upload_pdf.assert_called_once()
        mock_s3_client.generate_presigned_url.assert_called_once()

    @pytest.mark.asyncio
    async def test_rollback_on_failure(self, service, mock_projects_repo):
        """Transaction is rolled back if an error occurs."""
        project_id = str(uuid.uuid4())
        project = _make_project(project_id=uuid.UUID(project_id))
        status = _make_status(status_name="Not Applicable")

        mock_projects_repo.get_project_by_id.return_value = project
        mock_projects_repo.get_status_by_name.return_value = status
        mock_projects_repo.update_project_not_applicable.side_effect = RuntimeError("DB error")
        mock_projects_repo.rollback.return_value = None

        with pytest.raises(RuntimeError):
            await service.perform_action(
                project_id=project_id,
                action="mark_not_applicable",
                reason_category="Out of scope",
                comments="Comments",
                evidence_file=None,
                user_id="test_user",
            )

        mock_projects_repo.rollback.assert_called_once()


class TestPerformActionMarkComplete:
    """Tests for perform_action with mark_complete."""

    @pytest.mark.asyncio
    async def test_success(self, service, mock_projects_repo):
        """Successful mark_complete updates project status and completed_at."""
        project_id = str(uuid.uuid4())
        project = _make_project(project_id=uuid.UUID(project_id))
        status = _make_status(status_name="Completed")

        mock_projects_repo.get_project_by_id.return_value = project
        mock_projects_repo.get_status_by_name.return_value = status
        mock_projects_repo.update_project_complete.return_value = None
        mock_projects_repo.commit.return_value = None

        result = await service.perform_action(
            project_id=project_id,
            action="mark_complete",
            reason_category=None,
            comments=None,
            evidence_file=None,
            user_id="test_user",
        )

        assert result.status_code == 200
        assert result.message == "Action performed successfully"
        mock_projects_repo.update_project_complete.assert_called_once()
        mock_projects_repo.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_extra_fields_required(self, service, mock_projects_repo):
        """mark_complete does not require reason_category or comments."""
        project_id = str(uuid.uuid4())
        project = _make_project(project_id=uuid.UUID(project_id))
        status = _make_status(status_name="Completed")

        mock_projects_repo.get_project_by_id.return_value = project
        mock_projects_repo.get_status_by_name.return_value = status
        mock_projects_repo.update_project_complete.return_value = None
        mock_projects_repo.commit.return_value = None

        result = await service.perform_action(
            project_id=project_id,
            action="mark_complete",
            reason_category=None,
            comments=None,
            evidence_file=None,
            user_id="test_user",
        )

        assert result.status_code == 200

    @pytest.mark.asyncio
    async def test_rollback_on_failure(self, service, mock_projects_repo):
        """Transaction is rolled back on failure."""
        project_id = str(uuid.uuid4())
        project = _make_project(project_id=uuid.UUID(project_id))
        status = _make_status(status_name="Completed")

        mock_projects_repo.get_project_by_id.return_value = project
        mock_projects_repo.get_status_by_name.return_value = status
        mock_projects_repo.update_project_complete.side_effect = RuntimeError("DB error")
        mock_projects_repo.rollback.return_value = None

        with pytest.raises(RuntimeError):
            await service.perform_action(
                project_id=project_id,
                action="mark_complete",
                reason_category=None,
                comments=None,
                evidence_file=None,
                user_id="test_user",
            )

        mock_projects_repo.rollback.assert_called_once()


class TestPerformActionValidation:
    """Tests for perform_action input validation."""

    @pytest.mark.asyncio
    async def test_invalid_project_id_raises_error(self, service):
        """Invalid project_id format raises InvalidParameterError."""
        with pytest.raises(InvalidParameterError) as exc_info:
            await service.perform_action(
                project_id="not-a-uuid",
                action="mark_complete",
                reason_category=None,
                comments=None,
                evidence_file=None,
                user_id="test_user",
            )
        assert "project_id" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_empty_project_id_raises_error(self, service):
        """Empty project_id raises InvalidParameterError."""
        with pytest.raises(InvalidParameterError):
            await service.perform_action(
                project_id="",
                action="mark_complete",
                reason_category=None,
                comments=None,
                evidence_file=None,
                user_id="test_user",
            )

    @pytest.mark.asyncio
    async def test_invalid_action_raises_error(self, service):
        """Invalid action raises InvalidParameterError."""
        project_id = str(uuid.uuid4())
        with pytest.raises(InvalidParameterError) as exc_info:
            await service.perform_action(
                project_id=project_id,
                action="delete",
                reason_category=None,
                comments=None,
                evidence_file=None,
                user_id="test_user",
            )
        assert "action" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_project_not_found_raises_error(self, service, mock_projects_repo):
        """Non-existent project raises NotFoundError."""
        project_id = str(uuid.uuid4())
        mock_projects_repo.get_project_by_id.return_value = None

        with pytest.raises(NotFoundError) as exc_info:
            await service.perform_action(
                project_id=project_id,
                action="mark_complete",
                reason_category=None,
                comments=None,
                evidence_file=None,
                user_id="test_user",
            )
        assert "Project not found" in exc_info.value.message
