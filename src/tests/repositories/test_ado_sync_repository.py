"""Unit tests for AdoSyncRepository data access operations."""

import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.ado_sync_repository import AdoSyncRepository
from src.repositories.schema.artifact import Artifact
from src.repositories.schema.commit import Commit
from src.repositories.schema.cron_job import CronJob
from src.repositories.schema.devsecops_ticket import DevsecopsTicket
from src.repositories.schema.kpi_history import KpiHistory
from src.repositories.schema.pipeline_run import PipelineRun
from src.repositories.schema.project import Project
from src.repositories.schema.pull_request import PullRequest
from src.repositories.schema.repository import Repository
from src.repositories.schema.security_scan import SecurityScan


@pytest.fixture
def mock_session():
    """Create a mock async session."""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def repo(mock_session):
    """Create an AdoSyncRepository with mock session."""
    return AdoSyncRepository(mock_session)


class TestHasPendingAzureCronJob:
    """Tests for has_pending_azure_cron_job method."""

    @pytest.mark.asyncio
    async def test_has_pending_azure_cron_job_true(self, repo, mock_session):
        """Should return True when pending azure cron exists."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = CronJob(
            cron_id=uuid.uuid4(),
            type="azure",
            sync_status="pending",
        )
        mock_session.execute.return_value = mock_result

        result = await repo.has_pending_azure_cron_job()

        assert result is True

    @pytest.mark.asyncio
    async def test_has_pending_azure_cron_job_false(self, repo, mock_session):
        """Should return False when no pending azure cron."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await repo.has_pending_azure_cron_job()

        assert result is False


class TestCreateCronJob:
    """Tests for create_cron_job method."""

    @pytest.mark.asyncio
    async def test_create_cron_job_success(self, repo, mock_session):
        """Should create and return cron job with pending status."""
        created_by = "test_service"

        result = await repo.create_cron_job(created_by=created_by)

        assert result is not None
        mock_session.add.assert_called_once()
        mock_session.flush.assert_awaited_once()


class TestUpdateCronJobStatus:
    """Tests for update_cron_job_status method."""

    @pytest.mark.asyncio
    async def test_update_cron_job_status_success(self, repo, mock_session):
        """Should update cron job status."""
        cron_id = uuid.uuid4()
        status = "success"
        modified_by = "test_service"

        await repo.update_cron_job_status(cron_id, status, modified_by)

        mock_session.execute.assert_called_once()


class TestGetApplicableTickets:
    """Tests for get_applicable_tickets method."""

    @pytest.mark.asyncio
    async def test_get_applicable_tickets_returns_list(self, repo, mock_session):
        """Should return list of applicable devsecops tickets."""
        tickets = [
            DevsecopsTicket(
                ticket_id=uuid.uuid4(),
                project_id=uuid.uuid4(),
                specialization_id=uuid.uuid4(),
                is_active=1,
            ),
            DevsecopsTicket(
                ticket_id=uuid.uuid4(),
                project_id=uuid.uuid4(),
                specialization_id=uuid.uuid4(),
                is_active=1,
            ),
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = tickets
        mock_session.execute.return_value = mock_result

        result = await repo.get_applicable_tickets()

        assert len(result) == 2
        assert isinstance(result[0], DevsecopsTicket)

    @pytest.mark.asyncio
    async def test_get_applicable_tickets_empty(self, repo, mock_session):
        """Should return empty list when no applicable tickets."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        result = await repo.get_applicable_tickets()

        assert result == []


class TestGetRepositoriesForTicket:
    """Tests for get_repositories_for_ticket method."""

    @pytest.mark.asyncio
    async def test_get_repositories_for_ticket_returns_list(self, repo, mock_session):
        """Should return repositories linked to ticket."""
        ticket_id = uuid.uuid4()
        repos = [
            Repository(
                repository_id=uuid.uuid4(),
                ticket_id=ticket_id,
                repo_name="repo1",
                ado_repo_id="ado-123",
                is_active=1,
            ),
            Repository(
                repository_id=uuid.uuid4(),
                ticket_id=ticket_id,
                repo_name="repo2",
                ado_repo_id="ado-456",
                is_active=1,
            ),
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = repos
        mock_session.execute.return_value = mock_result

        result = await repo.get_repositories_for_ticket(ticket_id)

        assert len(result) == 2
        assert result[0].repo_name == "repo1"

    @pytest.mark.asyncio
    async def test_get_repositories_for_ticket_empty(self, repo, mock_session):
        """Should return empty list when no repositories."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        result = await repo.get_repositories_for_ticket(uuid.uuid4())

        assert result == []


class TestGetRepositoryById:
    """Tests for get_repository_by_id method."""

    @pytest.mark.asyncio
    async def test_get_repository_by_id_found(self, repo, mock_session):
        """Should return repository when found."""
        repository = Repository(
            repository_id=uuid.uuid4(),
            repo_name="test-repo",
            ado_repo_id="ado-789",
            is_active=1,
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = repository
        mock_session.execute.return_value = mock_result

        result = await repo.get_repository_by_id(repository.repository_id)

        assert result is not None
        assert result.repo_name == "test-repo"

    @pytest.mark.asyncio
    async def test_get_repository_by_id_not_found(self, repo, mock_session):
        """Should return None when repository not found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await repo.get_repository_by_id(uuid.uuid4())

        assert result is None


class TestSoftDeleteOperations:
    """Tests for soft delete operations."""

    @pytest.mark.asyncio
    async def test_soft_delete_pipeline_runs(self, repo, mock_session):
        """Should soft delete pipeline runs for repository."""
        repo_id = uuid.uuid4()

        await repo.soft_delete_pipeline_runs(repo_id)

        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_soft_delete_commits(self, repo, mock_session):
        """Should soft delete commits for repository."""
        repo_id = uuid.uuid4()

        await repo.soft_delete_commits(repo_id)

        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_soft_delete_pull_requests(self, repo, mock_session):
        """Should soft delete pull requests for repository."""
        repo_id = uuid.uuid4()

        await repo.soft_delete_pull_requests(repo_id)

        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_soft_delete_security_scans(self, repo, mock_session):
        """Should soft delete security scans for repository."""
        repo_id = uuid.uuid4()

        await repo.soft_delete_security_scans(repo_id)

        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_soft_delete_artifacts_for_repository(self, repo, mock_session):
        """Should soft delete artifacts for repository."""
        repo_id = uuid.uuid4()

        await repo.soft_delete_artifacts_for_repository(repo_id)

        mock_session.execute.assert_called_once()


class TestInsertOperations:
    """Tests for bulk insert operations."""

    @pytest.mark.asyncio
    async def test_insert_pipeline_runs(self, repo, mock_session):
        """Should bulk insert pipeline runs."""
        runs = [
            PipelineRun(
                repository_id=uuid.uuid4(),
                run_number=1,
                status="Succeeded",
                branch="main",
            ),
            PipelineRun(
                repository_id=uuid.uuid4(),
                run_number=2,
                status="Failed",
                branch="develop",
            ),
        ]

        await repo.insert_pipeline_runs(runs)

        mock_session.add_all.assert_called_once_with(runs)

    @pytest.mark.asyncio
    async def test_insert_commits(self, repo, mock_session):
        """Should bulk insert commits."""
        commits = [
            Commit(
                repository_id=uuid.uuid4(),
                commit_hash="abc123",
                author="John Doe",
                message="Fix bug",
            ),
        ]

        await repo.insert_commits(commits)

        mock_session.add_all.assert_called_once_with(commits)

    @pytest.mark.asyncio
    async def test_insert_pull_requests(self, repo, mock_session):
        """Should bulk insert pull requests."""
        prs = [
            PullRequest(
                repository_id=uuid.uuid4(),
                pr_number=1,
                title="Add feature",
                status="Completed",
            ),
        ]

        await repo.insert_pull_requests(prs)

        mock_session.add_all.assert_called_once_with(prs)

    @pytest.mark.asyncio
    async def test_insert_security_scans(self, repo, mock_session):
        """Should bulk insert security scans."""
        scans = [
            SecurityScan(
                repository_id=uuid.uuid4(),
                scan_type="SAST",
                findings_count=5,
            ),
        ]

        await repo.insert_security_scans(scans)

        mock_session.add_all.assert_called_once_with(scans)

    @pytest.mark.asyncio
    async def test_insert_artifacts(self, repo, mock_session):
        """Should bulk insert artifacts."""
        artifacts = [
            Artifact(
                pipeline_run_id=uuid.uuid4(),
                artifact_name="build.zip",
                artifact_type="Build",
            ),
        ]

        await repo.insert_artifacts(artifacts)

        mock_session.add_all.assert_called_once_with(artifacts)


class TestUpsertKpiHistory:
    """Tests for upsert_kpi_history method."""

    @pytest.mark.asyncio
    async def test_upsert_kpi_history_success(self, repo, mock_session):
        """Should upsert KPI history record."""
        kpi = KpiHistory(
            specialization_id=uuid.uuid4(),
            total_projects_count=100,
            adopted_count=40,
            completed_count=30,
            snapshot_date=datetime.utcnow().date(),
        )

        await repo.upsert_kpi_history(kpi)

        # Verify execute was called (merge/update statement)
        mock_session.execute.assert_called_once()


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
