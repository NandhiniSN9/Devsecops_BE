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
        mock_repos = [MagicMock(), MagicMock()]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_repos
        mock_session.execute.return_value = mock_result

        result = await repo.get_repositories_for_ticket(ticket_id)

        assert len(result) == 2

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
        mock_repo = MagicMock()
        mock_repo.repository_id = uuid.uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_repo
        mock_session.execute.return_value = mock_result

        result = await repo.get_repository_by_id(mock_repo.repository_id)

        assert result is not None

    @pytest.mark.asyncio
    async def test_get_repository_by_id_not_found(self, repo, mock_session):
        """Should return None when repository not found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await repo.get_repository_by_id(uuid.uuid4())

        assert result is None


class TestUpsertOperations:
    """Tests for upsert operations — update existing or insert new records."""

    @pytest.mark.asyncio
    async def test_upsert_pipeline_runs_updates_existing(self, repo, mock_session):
        """Should update existing pipeline run when run_number matches."""
        existing = MagicMock(spec=PipelineRun)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing
        mock_session.execute.return_value = mock_result

        run = PipelineRun(
            repository_id=uuid.uuid4(),
            run_number=1,
            status="passed",
            branch="main",
            triggered_at=datetime.utcnow(),
        )
        await repo.upsert_pipeline_runs([run])

        assert existing.status == "passed"
        assert existing.branch == "main"
        mock_session.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_upsert_pipeline_runs_inserts_new(self, repo, mock_session):
        """Should insert new pipeline run when run_number not found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        run = PipelineRun(
            repository_id=uuid.uuid4(),
            run_number=99,
            status="passed",
            branch="main",
            triggered_at=datetime.utcnow(),
        )
        await repo.upsert_pipeline_runs([run])

        mock_session.add.assert_called_once_with(run)
        mock_session.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_upsert_commits_updates_existing(self, repo, mock_session):
        """Should update existing commit when hash matches."""
        existing = MagicMock(spec=Commit)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing
        mock_session.execute.return_value = mock_result

        commit = Commit(
            repository_id=uuid.uuid4(),
            hash="abc123",
            message="updated message",
            author="Dev",
            committed_at=datetime.utcnow(),
        )
        await repo.upsert_commits([commit])

        assert existing.message == "updated message"
        mock_session.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_upsert_commits_inserts_new(self, repo, mock_session):
        """Should insert new commit when hash not found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        commit = Commit(
            repository_id=uuid.uuid4(),
            hash="newHash",
            message="new commit",
            author="Dev",
            committed_at=datetime.utcnow(),
        )
        await repo.upsert_commits([commit])

        mock_session.add.assert_called_once_with(commit)

    @pytest.mark.asyncio
    async def test_upsert_pull_requests_updates_existing(self, repo, mock_session):
        """Should update existing PR when title matches."""
        existing = MagicMock(spec=PullRequest)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing
        mock_session.execute.return_value = mock_result

        pr = PullRequest(
            repository_id=uuid.uuid4(),
            title="Add feature",
            author="Dev",
            status="merged",
        )
        await repo.upsert_pull_requests([pr])

        assert existing.status == "merged"
        mock_session.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_upsert_pull_requests_inserts_new(self, repo, mock_session):
        """Should insert new PR when title not found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        pr = PullRequest(
            repository_id=uuid.uuid4(),
            title="New PR",
            author="Dev",
            status="open",
        )
        await repo.upsert_pull_requests([pr])

        mock_session.add.assert_called_once_with(pr)

    @pytest.mark.asyncio
    async def test_upsert_security_scans_inserts(self, repo, mock_session):
        """Should insert new security scan records."""
        scan = SecurityScan(repository_id=uuid.uuid4())
        await repo.upsert_security_scans([scan])

        mock_session.add_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_upsert_artifacts_updates_existing(self, repo, mock_session):
        """Should update existing artifact when name matches."""
        existing = MagicMock(spec=Artifact)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing
        mock_session.execute.return_value = mock_result

        artifact = Artifact(
            pipeline_run_id=uuid.uuid4(),
            artifact_name="build.zip",
            size_bytes=1024,
            url="https://example.com/build.zip",
            uploaded_at=datetime.utcnow(),
        )
        await repo.upsert_artifacts([artifact])

        assert existing.size_bytes == 1024
        mock_session.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_upsert_artifacts_inserts_new(self, repo, mock_session):
        """Should insert new artifact when name not found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        artifact = Artifact(
            pipeline_run_id=uuid.uuid4(),
            artifact_name="new.zip",
            size_bytes=512,
            url="https://example.com/new.zip",
            uploaded_at=datetime.utcnow(),
        )
        await repo.upsert_artifacts([artifact])

        mock_session.add.assert_called_once_with(artifact)


class TestInsertKpiHistory:
    """Tests for insert_kpi_history method."""

    @pytest.mark.asyncio
    async def test_insert_kpi_history_success(self, repo, mock_session):
        """Should insert KPI history record."""
        kpi = KpiHistory(
            specialization_id=uuid.uuid4(),
            projects_count=10,
            completed_count=3,
            created_by="sync_ado_service",
        )

        await repo.insert_kpi_history(kpi)

        mock_session.add.assert_called_once_with(kpi)
        mock_session.flush.assert_awaited_once()


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
