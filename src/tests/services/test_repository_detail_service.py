"""Unit tests for RepositoryDetailService."""

import uuid
from datetime import datetime, date
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.repositories.repository_detail_repository import RepositoryDetailRepository
from src.services.repository_detail_service import RepositoryDetailService
from src.utils.exceptions import InvalidParameterError, NotFoundError


@pytest.fixture
def mock_repo():
    """Create a mock RepositoryDetailRepository."""
    return AsyncMock(spec=RepositoryDetailRepository)


@pytest.fixture
def service(mock_repo):
    """Create a RepositoryDetailService with mocked repository."""
    return RepositoryDetailService(repo=mock_repo)


def _make_repository(**kwargs):
    """Helper to create a mock Repository ORM object."""
    repo = MagicMock()
    repo.repository_id = kwargs.get("repository_id", uuid.uuid4())
    repo.repository_name = kwargs.get("repository_name", "test-repo")
    repo.ticket_id = kwargs.get("ticket_id", uuid.uuid4())
    repo.ado_repo_id = kwargs.get("ado_repo_id", "ado-123")
    repo.created_at = kwargs.get("created_at", datetime(2026, 2, 27))
    repo.pipeline_runs_count = kwargs.get("pipeline_runs_count", 10)
    repo.success_rate = kwargs.get("success_rate", 85.0)
    repo.last_run_at = kwargs.get("last_run_at", datetime(2026, 5, 7, 10, 30))
    repo.is_active = 1
    return repo


def _make_ticket(**kwargs):
    """Helper to create a mock DevsecopsTicket ORM object."""
    ticket = MagicMock()
    ticket.ticket_id = kwargs.get("ticket_id", uuid.uuid4())
    ticket.specialization_id = kwargs.get("specialization_id", uuid.uuid4())
    ticket.project_id = kwargs.get("project_id", uuid.uuid4())
    ticket.sn_project_id = kwargs.get("sn_project_id", "SN-001")
    ticket.requested_at = kwargs.get("requested_at", datetime(2026, 2, 20))
    return ticket


def _make_project(**kwargs):
    """Helper to create a mock Project ORM object."""
    project = MagicMock()
    project.project_id = kwargs.get("project_id", uuid.uuid4())
    project.project_name = kwargs.get("project_name", "Test Project")
    project.client = kwargs.get("client", "TestClient")
    project.project_type = kwargs.get("project_type", "Infrastructure")
    project.specialization_name = kwargs.get("specialization_name", "DevSecOps")
    project.completed_at = kwargs.get("completed_at", None)
    project.onboarded_date = kwargs.get("onboarded_date", date(2026, 2, 20))
    return project


def _make_pipeline_run(**kwargs):
    """Helper to create a mock PipelineRun ORM object."""
    run = MagicMock()
    run.pipeline_run_id = kwargs.get("pipeline_run_id", uuid.uuid4())
    run.run_number = kwargs.get("run_number", 1)
    run.status = kwargs.get("status", "passed")
    run.branch = kwargs.get("branch", "main")
    run.duration_seconds = kwargs.get("duration_seconds", 134)
    run.triggered_at = kwargs.get("triggered_at", datetime(2026, 5, 7, 10, 30))
    return run


class TestGetRepositoryDetail:
    """Tests for RepositoryDetailService.get_repository_detail."""

    @pytest.mark.asyncio
    async def test_invalid_uuid_raises_error(self, service):
        """Should raise InvalidParameterError for invalid UUID format."""
        with pytest.raises(InvalidParameterError) as exc_info:
            await service.get_repository_detail("not-a-uuid")
        assert "repository_id" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_repository_not_found_raises_error(self, service, mock_repo):
        """Should raise NotFoundError when repository doesn't exist."""
        mock_repo.get_repository_by_id.return_value = None

        with pytest.raises(NotFoundError) as exc_info:
            await service.get_repository_detail(str(uuid.uuid4()))
        assert "Repository not found" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_success_returns_full_detail(self, service, mock_repo):
        """Should return full repository detail for a valid repository."""
        repo_id = uuid.uuid4()
        ticket_id = uuid.uuid4()
        project_id = uuid.uuid4()

        repository = _make_repository(repository_id=repo_id, ticket_id=ticket_id)
        ticket = _make_ticket(ticket_id=ticket_id, project_id=project_id)
        project = _make_project(project_id=project_id)

        mock_repo.get_repository_by_id.return_value = repository
        mock_repo.get_ticket_for_repository.return_value = ticket
        mock_repo.get_project_by_id.return_value = project
        mock_repo.get_at_risk_threshold.return_value = 30
        mock_repo.get_total_pipeline_runs_count.return_value = 10
        mock_repo.get_last_30_pipeline_runs.return_value = []
        mock_repo.get_pipeline_runs.return_value = []
        mock_repo.get_commits.return_value = []
        mock_repo.get_pull_requests.return_value = []
        mock_repo.get_security_scans.return_value = []
        mock_repo.get_artifacts.return_value = []

        result = await service.get_repository_detail(str(repo_id))

        assert result.header.id == repo_id
        assert result.header.name == "test-repo"
        assert result.header.client == "TestClient"
        assert result.header.project.id == project_id
        assert result.pipeline_metrics.total_runs == 10
        assert len(result.adoption_timeline) == 4

    @pytest.mark.asyncio
    async def test_pipeline_metrics_with_runs(self, service, mock_repo):
        """Should calculate correct pipeline metrics when runs exist."""
        repo_id = uuid.uuid4()
        repository = _make_repository(repository_id=repo_id, ticket_id=None)

        runs = [
            _make_pipeline_run(status="passed", triggered_at=datetime(2026, 5, 7, 10, 30)),
            _make_pipeline_run(status="failed", triggered_at=datetime(2026, 5, 6, 10, 30)),
            _make_pipeline_run(status="passed", triggered_at=datetime(2026, 5, 5, 10, 30)),
        ]

        mock_repo.get_repository_by_id.return_value = repository
        mock_repo.get_ticket_for_repository.return_value = None
        mock_repo.get_total_pipeline_runs_count.return_value = 3
        mock_repo.get_last_30_pipeline_runs.return_value = runs
        mock_repo.get_pipeline_runs.return_value = runs
        mock_repo.get_commits.return_value = []
        mock_repo.get_pull_requests.return_value = []
        mock_repo.get_security_scans.return_value = []
        mock_repo.get_artifacts.return_value = []

        result = await service.get_repository_detail(str(repo_id))

        assert result.pipeline_metrics.total_runs == 3
        assert result.pipeline_metrics.success_rate == 66.7
        assert result.pipeline_metrics.last_pipeline_run_at == datetime(2026, 5, 7, 10, 30)

    @pytest.mark.asyncio
    async def test_adoption_timeline_no_runs(self, service, mock_repo):
        """Should return correct timeline when no pipeline runs exist."""
        repo_id = uuid.uuid4()
        repository = _make_repository(repository_id=repo_id, ticket_id=None)

        mock_repo.get_repository_by_id.return_value = repository
        mock_repo.get_ticket_for_repository.return_value = None
        mock_repo.get_total_pipeline_runs_count.return_value = 0
        mock_repo.get_last_30_pipeline_runs.return_value = []
        mock_repo.get_pipeline_runs.return_value = []
        mock_repo.get_commits.return_value = []
        mock_repo.get_pull_requests.return_value = []
        mock_repo.get_security_scans.return_value = []
        mock_repo.get_artifacts.return_value = []

        result = await service.get_repository_detail(str(repo_id))

        timeline = result.adoption_timeline
        assert timeline[0].step == "kicked_off"
        assert timeline[0].status == "completed"
        assert timeline[1].step == "pipeline_detected"
        assert timeline[1].status == "in_progress"
        assert timeline[2].step == "first_run"
        assert timeline[2].status == "pending"
        assert timeline[3].step == "adopted"
        assert timeline[3].status == "pending"

    @pytest.mark.asyncio
    async def test_security_scans_aggregation(self, service, mock_repo):
        """Should correctly aggregate security scan findings."""
        repo_id = uuid.uuid4()
        repository = _make_repository(repository_id=repo_id, ticket_id=None)

        scan1 = MagicMock(scan_type="SCA", findings_count=5)
        scan2 = MagicMock(scan_type="SAST", findings_count=3)
        scan3 = MagicMock(scan_type="DAST", findings_count=2)

        mock_repo.get_repository_by_id.return_value = repository
        mock_repo.get_ticket_for_repository.return_value = None
        mock_repo.get_total_pipeline_runs_count.return_value = 0
        mock_repo.get_last_30_pipeline_runs.return_value = []
        mock_repo.get_pipeline_runs.return_value = []
        mock_repo.get_commits.return_value = []
        mock_repo.get_pull_requests.return_value = []
        mock_repo.get_security_scans.return_value = [scan1, scan2, scan3]
        mock_repo.get_artifacts.return_value = []

        result = await service.get_repository_detail(str(repo_id))

        assert result.security_scans.total_findings == 10
        assert result.security_scans.sca.count == 5
        assert result.security_scans.sast.count == 3
        assert result.security_scans.dast.count == 2


class TestFormatDuration:
    """Tests for RepositoryDetailService._format_duration."""

    def test_none_returns_zero(self, service):
        assert service._format_duration(None) == "0s"

    def test_seconds_only(self, service):
        assert service._format_duration(45) == "45s"

    def test_minutes_and_seconds(self, service):
        assert service._format_duration(134) == "2m 14s"

    def test_hours_and_minutes(self, service):
        assert service._format_duration(3780) == "1h 3m"

    def test_exact_minutes(self, service):
        assert service._format_duration(120) == "2m"


class TestFormatFileSize:
    """Tests for RepositoryDetailService._format_file_size."""

    def test_bytes(self, service):
        assert service._format_file_size(500) == "500 B"

    def test_kilobytes(self, service):
        assert service._format_file_size(1536) == "1.5 KB"

    def test_megabytes(self, service):
        assert service._format_file_size(4404019) == "4.2 MB"

    def test_gigabytes(self, service):
        assert service._format_file_size(1073741824) == "1.0 GB"
