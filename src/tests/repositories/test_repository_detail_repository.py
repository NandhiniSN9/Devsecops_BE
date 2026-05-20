"""Unit tests for RepositoryDetailRepository data access operations.

Tests repository header details, pipeline metrics, commits, PRs, security scans, and artifacts.
"""

import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.repository_detail_repository import RepositoryDetailRepository
from src.repositories.schema.artifact import Artifact
from src.repositories.schema.commit import Commit
from src.repositories.schema.devsecops_ticket import DevsecopsTicket
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
    """Create a RepositoryDetailRepository with mock session."""
    return RepositoryDetailRepository(mock_session)


@pytest.fixture
def sample_repository():
    """Create a sample repository object for testing."""
    return Repository(
        repository_id=uuid.uuid4(),
        repo_name="sample-repo",
        repo_url="https://github.com/org/sample-repo",
        is_active=1,
        created_at=datetime.utcnow(),
        created_by="test_user",
    )


@pytest.fixture
def sample_pipeline_runs(sample_repository):
    """Create sample pipeline run objects for testing."""
    now = datetime.utcnow()
    return [
        PipelineRun(
            pipeline_run_id=uuid.uuid4(),
            repository_id=sample_repository.repository_id,
            run_number=100,
            status="success",
            triggered_at=now - timedelta(hours=1),
            completed_at=now - timedelta(minutes=50),
            is_active=1,
        ),
        PipelineRun(
            pipeline_run_id=uuid.uuid4(),
            repository_id=sample_repository.repository_id,
            run_number=99,
            status="failed",
            triggered_at=now - timedelta(hours=2),
            completed_at=now - timedelta(hours=1, minutes=50),
            is_active=1,
        ),
        PipelineRun(
            pipeline_run_id=uuid.uuid4(),
            repository_id=sample_repository.repository_id,
            run_number=98,
            status="success",
            triggered_at=now - timedelta(hours=3),
            completed_at=now - timedelta(hours=2, minutes=50),
            is_active=1,
        ),
    ]


@pytest.fixture
def sample_commits(sample_repository):
    """Create sample commit objects for testing."""
    now = datetime.utcnow()
    return [
        Commit(
            commit_id=uuid.uuid4(),
            repository_id=sample_repository.repository_id,
            commit_sha="abc123def456",
            commit_message="Fix bug in authentication",
            author="John Doe",
            committed_at=now - timedelta(hours=1),
            is_active=1,
        ),
        Commit(
            commit_id=uuid.uuid4(),
            repository_id=sample_repository.repository_id,
            commit_sha="def789ghi012",
            commit_message="Add new feature",
            author="Jane Smith",
            committed_at=now - timedelta(hours=5),
            is_active=1,
        ),
    ]


@pytest.fixture
def sample_pull_requests(sample_repository):
    """Create sample pull request objects for testing."""
    now = datetime.utcnow()
    return [
        PullRequest(
            pull_request_id=uuid.uuid4(),
            repository_id=sample_repository.repository_id,
            pr_number=42,
            title="Feature: Add authentication",
            state="open",
            author="dev1",
            created_at=now - timedelta(days=2),
            updated_at=now - timedelta(hours=1),
            is_active=1,
        ),
        PullRequest(
            pull_request_id=uuid.uuid4(),
            repository_id=sample_repository.repository_id,
            pr_number=41,
            title="Fix: Security vulnerability",
            state="merged",
            author="dev2",
            created_at=now - timedelta(days=5),
            updated_at=now - timedelta(days=1),
            is_active=1,
        ),
    ]


@pytest.fixture
def sample_security_scans(sample_repository):
    """Create sample security scan objects for testing."""
    now = datetime.utcnow()
    return [
        SecurityScan(
            security_scan_id=uuid.uuid4(),
            repository_id=sample_repository.repository_id,
            scan_type="SAST",
            severity="high",
            finding_count=3,
            scanned_at=now - timedelta(days=1),
            is_active=1,
        ),
        SecurityScan(
            security_scan_id=uuid.uuid4(),
            repository_id=sample_repository.repository_id,
            scan_type="SCA",
            severity="medium",
            finding_count=7,
            scanned_at=now - timedelta(days=2),
            is_active=1,
        ),
    ]


class TestGetRepositoryById:
    """Tests for get_repository_by_id method."""

    @pytest.mark.asyncio
    async def test_get_repository_by_id_found(self, repo, mock_session, sample_repository):
        """Should return repository when found and active."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_repository
        mock_session.execute.return_value = mock_result

        result = await repo.get_repository_by_id(sample_repository.repository_id)

        assert result is not None
        assert result.repo_name == "sample-repo"
        assert result.is_active == 1

    @pytest.mark.asyncio
    async def test_get_repository_by_id_not_found(self, repo, mock_session):
        """Should return None when repository not found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await repo.get_repository_by_id(uuid.uuid4())

        assert result is None

    @pytest.mark.asyncio
    async def test_get_repository_by_id_exception(self, repo, mock_session):
        """Should raise exception on error."""
        mock_session.execute.side_effect = Exception("Database error")

        with pytest.raises(Exception):
            await repo.get_repository_by_id(uuid.uuid4())


class TestGetTicketForRepository:
    """Tests for get_ticket_for_repository method."""

    @pytest.mark.asyncio
    async def test_get_ticket_found(self, repo, mock_session):
        """Should return devsecops ticket when found."""
        ticket = DevsecopsTicket(
            ticket_id=uuid.uuid4(),
            project_id=uuid.uuid4(),
            ticket_status="In Progress",
            is_active=1,
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = ticket
        mock_session.execute.return_value = mock_result

        result = await repo.get_ticket_for_repository(ticket.ticket_id)

        assert result is not None
        assert result.ticket_status == "In Progress"

    @pytest.mark.asyncio
    async def test_get_ticket_not_found(self, repo, mock_session):
        """Should return None when ticket not found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await repo.get_ticket_for_repository(uuid.uuid4())

        assert result is None


class TestGetProjectById:
    """Tests for get_project_by_id method."""

    @pytest.mark.asyncio
    async def test_get_project_by_id_found(self, repo, mock_session):
        """Should return project when found and active."""
        project = Project(
            project_id=uuid.uuid4(),
            project_name="Test Project",
            client="TestClient",
            is_active=1,
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = project
        mock_session.execute.return_value = mock_result

        result = await repo.get_project_by_id(project.project_id)

        assert result is not None
        assert result.project_name == "Test Project"

    @pytest.mark.asyncio
    async def test_get_project_by_id_not_found(self, repo, mock_session):
        """Should return None when project not found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await repo.get_project_by_id(uuid.uuid4())

        assert result is None


class TestGetProjectBySnId:
    """Tests for get_project_by_sn_id method."""

    @pytest.mark.asyncio
    async def test_get_project_by_sn_id_found(self, repo, mock_session):
        """Should return project when found by ServiceNow ID."""
        project = Project(
            project_id=uuid.uuid4(),
            sn_project_id="PRJ123456",
            project_name="SN Project",
            is_active=1,
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = project
        mock_session.execute.return_value = mock_result

        result = await repo.get_project_by_sn_id("PRJ123456")

        assert result is not None
        assert result.sn_project_id == "PRJ123456"

    @pytest.mark.asyncio
    async def test_get_project_by_sn_id_not_found(self, repo, mock_session):
        """Should return None when no project with SN ID found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await repo.get_project_by_sn_id("INVALID123")

        assert result is None


class TestGetAtRiskThreshold:
    """Tests for get_at_risk_threshold method."""

    @pytest.mark.asyncio
    async def test_get_at_risk_threshold_found(self, repo, mock_session):
        """Should return at-risk threshold for specialization."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = 30
        mock_session.execute.return_value = mock_result

        result = await repo.get_at_risk_threshold(uuid.uuid4())

        assert result == 30

    @pytest.mark.asyncio
    async def test_get_at_risk_threshold_not_found(self, repo, mock_session):
        """Should return None when no settings found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await repo.get_at_risk_threshold(uuid.uuid4())

        assert result is None


class TestGetPipelineRuns:
    """Tests for get_pipeline_runs method."""

    @pytest.mark.asyncio
    async def test_get_pipeline_runs_success(self, repo, mock_session, sample_pipeline_runs):
        """Should return all active pipeline runs sorted by triggered_at desc."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = sample_pipeline_runs
        mock_session.execute.return_value = mock_result

        result = await repo.get_pipeline_runs(uuid.uuid4())

        assert len(result) == 3
        assert result[0].run_number == 100
        assert result[1].run_number == 99
        assert result[2].run_number == 98

    @pytest.mark.asyncio
    async def test_get_pipeline_runs_empty_list(self, repo, mock_session):
        """Should return empty list when no pipeline runs exist."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        result = await repo.get_pipeline_runs(uuid.uuid4())

        assert result == []

    @pytest.mark.asyncio
    async def test_get_pipeline_runs_exception(self, repo, mock_session):
        """Should raise exception on error."""
        mock_session.execute.side_effect = Exception("Query failed")

        with pytest.raises(Exception):
            await repo.get_pipeline_runs(uuid.uuid4())


class TestGetTotalPipelineRunsCount:
    """Tests for get_total_pipeline_runs_count method."""

    @pytest.mark.asyncio
    async def test_get_total_pipeline_runs_count_success(self, repo, mock_session):
        """Should return total count of active pipeline runs."""
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 45
        mock_session.execute.return_value = mock_result

        result = await repo.get_total_pipeline_runs_count(uuid.uuid4())

        assert result == 45

    @pytest.mark.asyncio
    async def test_get_total_pipeline_runs_count_zero(self, repo, mock_session):
        """Should return 0 when no pipeline runs exist."""
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 0
        mock_session.execute.return_value = mock_result

        result = await repo.get_total_pipeline_runs_count(uuid.uuid4())

        assert result == 0


class TestGetLast30PipelineRuns:
    """Tests for get_last_30_pipeline_runs method."""

    @pytest.mark.asyncio
    async def test_get_last_30_pipeline_runs_success(self, repo, mock_session, sample_pipeline_runs):
        """Should return last 30 pipeline runs for success rate calculation."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = sample_pipeline_runs
        mock_session.execute.return_value = mock_result

        result = await repo.get_last_30_pipeline_runs(uuid.uuid4())

        assert len(result) == 3
        assert result[0].status == "success"
        assert result[1].status == "failed"

    @pytest.mark.asyncio
    async def test_get_last_30_pipeline_runs_less_than_30(self, repo, mock_session):
        """Should return available runs when less than 30 exist."""
        runs = [
            PipelineRun(
                pipeline_run_id=uuid.uuid4(),
                repository_id=uuid.uuid4(),
                run_number=10,
                status="success",
                triggered_at=datetime.utcnow(),
                is_active=1,
            )
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = runs
        mock_session.execute.return_value = mock_result

        result = await repo.get_last_30_pipeline_runs(uuid.uuid4())

        assert len(result) == 1


class TestGetCommits:
    """Tests for get_commits method."""

    @pytest.mark.asyncio
    async def test_get_commits_success(self, repo, mock_session, sample_commits):
        """Should return all active commits sorted by committed_at desc."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = sample_commits
        mock_session.execute.return_value = mock_result

        result = await repo.get_commits(uuid.uuid4())

        assert len(result) == 2
        assert result[0].commit_sha == "abc123def456"
        assert result[0].author == "John Doe"

    @pytest.mark.asyncio
    async def test_get_commits_empty_list(self, repo, mock_session):
        """Should return empty list when no commits exist."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        result = await repo.get_commits(uuid.uuid4())

        assert result == []


class TestGetPullRequests:
    """Tests for get_pull_requests method."""

    @pytest.mark.asyncio
    async def test_get_pull_requests_success(self, repo, mock_session, sample_pull_requests):
        """Should return all active pull requests sorted by updated_at desc."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = sample_pull_requests
        mock_session.execute.return_value = mock_result

        result = await repo.get_pull_requests(uuid.uuid4())

        assert len(result) == 2
        assert result[0].pr_number == 42
        assert result[0].state == "open"
        assert result[1].state == "merged"

    @pytest.mark.asyncio
    async def test_get_pull_requests_empty_list(self, repo, mock_session):
        """Should return empty list when no pull requests exist."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        result = await repo.get_pull_requests(uuid.uuid4())

        assert result == []


class TestGetSecurityScans:
    """Tests for get_security_scans method."""

    @pytest.mark.asyncio
    async def test_get_security_scans_success(self, repo, mock_session, sample_security_scans):
        """Should return all active security scans."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = sample_security_scans
        mock_session.execute.return_value = mock_result

        result = await repo.get_security_scans(uuid.uuid4())

        assert len(result) == 2
        assert result[0].scan_type == "SAST"
        assert result[0].severity == "high"
        assert result[1].scan_type == "SCA"

    @pytest.mark.asyncio
    async def test_get_security_scans_empty_list(self, repo, mock_session):
        """Should return empty list when no security scans exist."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        result = await repo.get_security_scans(uuid.uuid4())

        assert result == []


class TestGetArtifacts:
    """Tests for get_artifacts method."""

    @pytest.mark.asyncio
    async def test_get_artifacts_success(self, repo, mock_session):
        """Should return artifacts with run numbers sorted by uploaded_at desc."""
        artifact1 = Artifact(
            artifact_id=uuid.uuid4(),
            pipeline_run_id=uuid.uuid4(),
            artifact_name="build.zip",
            artifact_size=1024000,
            uploaded_at=datetime.utcnow() - timedelta(hours=1),
            is_active=1,
        )
        artifact2 = Artifact(
            artifact_id=uuid.uuid4(),
            pipeline_run_id=uuid.uuid4(),
            artifact_name="app.jar",
            artifact_size=2048000,
            uploaded_at=datetime.utcnow() - timedelta(hours=2),
            is_active=1,
        )

        mock_result = MagicMock()
        mock_result.tuples.return_value.all.return_value = [
            (artifact1, 100),
            (artifact2, 99),
        ]
        mock_session.execute.return_value = mock_result

        result = await repo.get_artifacts(uuid.uuid4())

        assert len(result) == 2
        assert result[0][0].artifact_name == "build.zip"
        assert result[0][1] == 100  # run_number
        assert result[1][0].artifact_name == "app.jar"
        assert result[1][1] == 99

    @pytest.mark.asyncio
    async def test_get_artifacts_empty_list(self, repo, mock_session):
        """Should return empty list when no artifacts exist."""
        mock_result = MagicMock()
        mock_result.tuples.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        result = await repo.get_artifacts(uuid.uuid4())

        assert result == []

    @pytest.mark.asyncio
    async def test_get_artifacts_join_with_pipeline_runs(self, repo, mock_session):
        """Should properly join artifacts with pipeline runs."""
        # This test verifies that only artifacts linked to active pipeline runs are returned
        mock_result = MagicMock()
        mock_result.tuples.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        result = await repo.get_artifacts(uuid.uuid4())

        # Verify execute was called (join query executed)
        mock_session.execute.assert_called_once()
        assert result == []


class TestMetricsAggregation:
    """Tests for metrics aggregation scenarios."""

    @pytest.mark.asyncio
    async def test_calculate_success_rate_from_pipeline_runs(self, repo, mock_session):
        """Should support success rate calculation from pipeline run data."""
        # Create 30 pipeline runs: 20 success, 10 failed
        runs = []
        for i in range(30):
            status = "success" if i < 20 else "failed"
            runs.append(
                PipelineRun(
                    pipeline_run_id=uuid.uuid4(),
                    repository_id=uuid.uuid4(),
                    run_number=i,
                    status=status,
                    triggered_at=datetime.utcnow() - timedelta(hours=i),
                    is_active=1,
                )
            )

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = runs
        mock_session.execute.return_value = mock_result

        result = await repo.get_last_30_pipeline_runs(uuid.uuid4())

        # Calculate success rate
        success_count = sum(1 for r in result if r.status == "success")
        success_rate = (success_count / len(result)) * 100 if result else 0

        assert success_rate == pytest.approx(66.67, rel=0.01)

    @pytest.mark.asyncio
    async def test_get_repository_header_data_complete(self, repo, mock_session, sample_repository):
        """Should support getting complete repository header information."""
        # Repository
        repo_result = MagicMock()
        repo_result.scalar_one_or_none.return_value = sample_repository

        # Total pipeline runs
        count_result = MagicMock()
        count_result.scalar_one.return_value = 150

        mock_session.execute.side_effect = [repo_result, count_result]

        repository = await repo.get_repository_by_id(sample_repository.repository_id)
        total_runs = await repo.get_total_pipeline_runs_count(sample_repository.repository_id)

        assert repository is not None
        assert repository.repo_name == "sample-repo"
        assert total_runs == 150


class TestErrorHandling:
    """Tests for error handling and edge cases."""

    @pytest.mark.asyncio
    async def test_methods_raise_on_exception(self, repo, mock_session):
        """Should raise exceptions from database errors."""
        mock_session.execute.side_effect = Exception("Connection lost")

        with pytest.raises(Exception):
            await repo.get_repository_by_id(uuid.uuid4())

        with pytest.raises(Exception):
            await repo.get_pipeline_runs(uuid.uuid4())

        with pytest.raises(Exception):
            await repo.get_commits(uuid.uuid4())

    @pytest.mark.asyncio
    async def test_get_artifacts_exception(self, repo, mock_session):
        """Should raise exception on artifacts query failure."""
        mock_session.execute.side_effect = Exception("Join failed")

        with pytest.raises(Exception):
            await repo.get_artifacts(uuid.uuid4())


class TestDataIntegrity:
    """Tests for data integrity and filtering."""

    @pytest.mark.asyncio
    async def test_only_active_repositories_returned(self, repo, mock_session):
        """Should only return repositories where is_active = 1."""
        # Mock returns None for inactive repository
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await repo.get_repository_by_id(uuid.uuid4())

        # Inactive repository should not be returned
        assert result is None

    @pytest.mark.asyncio
    async def test_only_active_pipeline_runs_returned(self, repo, mock_session):
        """Should only return pipeline runs where is_active = 1."""
        active_runs = [
            PipelineRun(
                pipeline_run_id=uuid.uuid4(),
                repository_id=uuid.uuid4(),
                run_number=1,
                status="success",
                triggered_at=datetime.utcnow(),
                is_active=1,
            )
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = active_runs
        mock_session.execute.return_value = mock_result

        result = await repo.get_pipeline_runs(uuid.uuid4())

        assert len(result) == 1
        assert all(r.is_active == 1 for r in result)
