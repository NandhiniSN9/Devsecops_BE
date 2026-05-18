"""Unit tests for AdoSyncService."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.client.ado_client import AdoClient
from src.repositories.ado_sync_repository import AdoSyncRepository
from src.services.ado_sync_service import AdoSyncService


@pytest.fixture
def mock_repo():
    """Create a mock AdoSyncRepository."""
    repo = AsyncMock(spec=AdoSyncRepository)
    repo.commit = AsyncMock()
    repo.rollback = AsyncMock()
    return repo


@pytest.fixture
def mock_ado_client():
    """Create a mock AdoClient."""
    return AsyncMock(spec=AdoClient)


@pytest.fixture
def service(mock_repo, mock_ado_client):
    """Create an AdoSyncService with mocked dependencies."""
    return AdoSyncService(repo=mock_repo, ado_client=mock_ado_client)


def _make_cron_job():
    """Helper to create a mock CronJob."""
    cron = MagicMock()
    cron.cron_id = uuid.uuid4()
    return cron


def _make_project(**kwargs):
    """Helper to create a mock Project."""
    project = MagicMock()
    project.project_id = kwargs.get("project_id", uuid.uuid4())
    project.project_name = kwargs.get("project_name", "Test Project")
    return project


def _make_repository(**kwargs):
    """Helper to create a mock Repository."""
    repo = MagicMock()
    repo.repository_id = kwargs.get("repository_id", uuid.uuid4())
    repo.repository_name = kwargs.get("repository_name", "test-repo")
    repo.ado_repo_id = kwargs.get("ado_repo_id", "ado-123")
    repo.pipeline_runs_count = kwargs.get("pipeline_runs_count", 0)
    repo.last_run_at = kwargs.get("last_run_at", None)
    return repo


class TestSyncAdoData:
    """Tests for AdoSyncService.sync_ado_data."""

    @pytest.mark.asyncio
    async def test_creates_cron_job_and_completes(self, service, mock_repo, mock_ado_client):
        """Should create a cron job and complete sync successfully."""
        cron_job = _make_cron_job()
        mock_repo.create_cron_job.return_value = cron_job
        mock_repo.get_applicable_projects.return_value = []

        result = await service.sync_ado_data()

        assert result == "Sync completed successfully"
        mock_repo.create_cron_job.assert_called_once()
        mock_repo.update_cron_job_status.assert_called_once_with(
            cron_job.cron_id, "success", "sync_ado_service"
        )

    @pytest.mark.asyncio
    async def test_skips_repos_without_ado_repo_id(self, service, mock_repo, mock_ado_client):
        """Should skip repositories without ado_repo_id."""
        cron_job = _make_cron_job()
        project = _make_project()
        repo_no_ado = _make_repository(ado_repo_id=None)

        mock_repo.create_cron_job.return_value = cron_job
        mock_repo.get_applicable_projects.return_value = [project]
        mock_repo.get_repositories_for_project.return_value = [repo_no_ado]
        mock_repo.get_specialization_ids_for_project.return_value = []

        await service.sync_ado_data()

        # ADO client should not be called
        mock_ado_client.get_pipeline_runs.assert_not_called()

    @pytest.mark.asyncio
    async def test_syncs_repository_with_ado_data(self, service, mock_repo, mock_ado_client):
        """Should fetch and insert data for repositories with ado_repo_id."""
        cron_job = _make_cron_job()
        project = _make_project()
        repository = _make_repository(ado_repo_id="ado-456")

        mock_repo.create_cron_job.return_value = cron_job
        mock_repo.get_applicable_projects.return_value = [project]
        mock_repo.get_repositories_for_project.return_value = [repository]
        mock_repo.get_specialization_ids_for_project.return_value = []

        mock_ado_client.get_pipeline_runs.return_value = [
            {
                "buildNumber": 42,
                "result": "succeeded",
                "sourceBranch": "refs/heads/main",
                "startTime": "2026-05-07T10:00:00Z",
                "finishTime": "2026-05-07T10:02:14Z",
                "queueTime": "2026-05-07T09:59:00Z",
                "id": 100,
            }
        ]
        mock_ado_client.get_commits.return_value = [
            {
                "commitId": "abc123def456",
                "comment": "feat: add pipeline",
                "author": {"name": "Tom Walsh", "date": "2026-05-07T09:15:00Z"},
            }
        ]
        mock_ado_client.get_pull_requests.return_value = [
            {
                "title": "Add pipeline template",
                "createdBy": {"displayName": "Tom Walsh"},
                "status": "active",
                "creationDate": "2026-05-06T14:00:00Z",
            }
        ]
        mock_ado_client.get_build_artifacts.return_value = []

        await service.sync_ado_data()

        mock_repo.soft_delete_pipeline_runs.assert_called_once()
        mock_repo.soft_delete_commits.assert_called_once()
        mock_repo.soft_delete_pull_requests.assert_called_once()
        mock_repo.insert_pipeline_runs.assert_called_once()
        mock_repo.insert_commits.assert_called_once()
        mock_repo.insert_pull_requests.assert_called_once()
        mock_repo.update_repository_metrics.assert_called_once()

    @pytest.mark.asyncio
    async def test_handles_repo_sync_failure_gracefully(self, service, mock_repo, mock_ado_client):
        """Should continue sync when individual repository fails."""
        cron_job = _make_cron_job()
        project = _make_project()
        repo1 = _make_repository(ado_repo_id="ado-1")
        repo2 = _make_repository(ado_repo_id="ado-2")

        mock_repo.create_cron_job.return_value = cron_job
        mock_repo.get_applicable_projects.return_value = [project]
        mock_repo.get_repositories_for_project.return_value = [repo1, repo2]
        mock_repo.get_specialization_ids_for_project.return_value = []

        # First repo fails, second succeeds
        mock_ado_client.get_pipeline_runs.side_effect = [
            Exception("ADO API error"),
            [],
        ]
        mock_ado_client.get_commits.return_value = []
        mock_ado_client.get_pull_requests.return_value = []

        await service.sync_ado_data()

        # Cron job should be marked as "fail" due to error
        mock_repo.update_cron_job_status.assert_called_once_with(
            cron_job.cron_id, "fail", "sync_ado_service"
        )

    @pytest.mark.asyncio
    async def test_filters_by_specialization_id(self, service, mock_repo, mock_ado_client):
        """Should pass specialization_id to repository query."""
        spec_id = uuid.uuid4()
        cron_job = _make_cron_job()

        mock_repo.create_cron_job.return_value = cron_job
        mock_repo.get_applicable_projects.return_value = []

        await service.sync_ado_data(specialization_id=spec_id)

        mock_repo.get_applicable_projects.assert_called_once_with(spec_id)


class TestMapBuildStatus:
    """Tests for AdoSyncService._map_build_status."""

    def test_succeeded(self, service):
        assert service._map_build_status("succeeded") == "passed"

    def test_failed(self, service):
        assert service._map_build_status("failed") == "failed"

    def test_canceled(self, service):
        assert service._map_build_status("canceled") == "cancelled"

    def test_unknown_defaults_to_running(self, service):
        assert service._map_build_status("inProgress") == "running"


class TestMapPrStatus:
    """Tests for AdoSyncService._map_pr_status."""

    def test_active(self, service):
        assert service._map_pr_status("active") == "open"

    def test_completed(self, service):
        assert service._map_pr_status("completed") == "merged"

    def test_abandoned(self, service):
        assert service._map_pr_status("abandoned") == "declined"


class TestStripBranchPrefix:
    """Tests for AdoSyncService._strip_branch_prefix."""

    def test_strips_refs_heads(self, service):
        assert service._strip_branch_prefix("refs/heads/main") == "main"

    def test_no_prefix_unchanged(self, service):
        assert service._strip_branch_prefix("feature/test") == "feature/test"
