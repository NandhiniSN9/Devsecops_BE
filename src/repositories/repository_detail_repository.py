"""Repository for repository detail data access operations."""

import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.schema.artifact import Artifact
from src.repositories.schema.commit import Commit
from src.repositories.schema.devsecops_ticket import DevsecopsTicket
from src.repositories.schema.pipeline_run import PipelineRun
from src.repositories.schema.project import Project
from src.repositories.schema.pull_request import PullRequest
from src.repositories.schema.repository import Repository
from src.repositories.schema.security_scan import SecurityScan
from src.repositories.schema.setting import Setting


class RepositoryDetailRepository:
    """Data access layer for repository detail queries."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_repository_by_id(self, repository_id: uuid.UUID) -> Repository | None:
        """Get an active repository by ID.

        Args:
            repository_id: UUID of the repository.

        Returns:
            Repository record or None if not found/inactive.
        """
        stmt = select(Repository).where(
            Repository.repository_id == repository_id,
            Repository.is_active == 1,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_ticket_for_repository(self, ticket_id: uuid.UUID) -> DevsecopsTicket | None:
        """Get the devsecops ticket linked to a repository."""
        stmt = select(DevsecopsTicket).where(
            DevsecopsTicket.ticket_id == ticket_id,
            DevsecopsTicket.is_active == 1,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_project_by_id(self, project_id: uuid.UUID) -> Project | None:
        """Get an active project by ID."""
        stmt = select(Project).where(
            Project.project_id == project_id,
            Project.is_active == 1,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_project_by_sn_id(self, sn_project_id: str) -> Project | None:
        """Get an active project by ServiceNow project ID."""
        stmt = select(Project).where(
            Project.sn_project_id == sn_project_id,
            Project.is_active == 1,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_at_risk_threshold(self, specialization_id: uuid.UUID) -> int | None:
        """Get the at-risk threshold for a specialization from settings."""
        stmt = select(Setting.at_risk_threshold).where(
            Setting.specialization_id == specialization_id,
            Setting.is_active == 1,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_pipeline_runs(self, repository_id: uuid.UUID) -> list[PipelineRun]:
        """Get all active pipeline runs for a repository, sorted by triggered_at desc."""
        stmt = (
            select(PipelineRun)
            .where(
                PipelineRun.repository_id == repository_id,
                PipelineRun.is_active == 1,
            )
            .order_by(PipelineRun.triggered_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_total_pipeline_runs_count(self, repository_id: uuid.UUID) -> int:
        """Get total count of active pipeline runs for a repository."""
        stmt = (
            select(func.count())
            .select_from(PipelineRun)
            .where(
                PipelineRun.repository_id == repository_id,
                PipelineRun.is_active == 1,
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def get_last_30_pipeline_runs(self, repository_id: uuid.UUID) -> list[PipelineRun]:
        """Get the last 30 pipeline runs for success rate calculation."""
        stmt = (
            select(PipelineRun)
            .where(
                PipelineRun.repository_id == repository_id,
                PipelineRun.is_active == 1,
            )
            .order_by(PipelineRun.triggered_at.desc())
            .limit(30)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_commits(self, repository_id: uuid.UUID) -> list[Commit]:
        """Get all active commits for a repository, sorted by committed_at desc."""
        stmt = (
            select(Commit)
            .where(
                Commit.repository_id == repository_id,
                Commit.is_active == 1,
            )
            .order_by(Commit.committed_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_pull_requests(self, repository_id: uuid.UUID) -> list[PullRequest]:
        """Get all active pull requests for a repository, sorted by updated_at desc."""
        stmt = (
            select(PullRequest)
            .where(
                PullRequest.repository_id == repository_id,
                PullRequest.is_active == 1,
            )
            .order_by(PullRequest.updated_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_security_scans(self, repository_id: uuid.UUID) -> list[SecurityScan]:
        """Get all active security scans for a repository."""
        stmt = (
            select(SecurityScan)
            .where(
                SecurityScan.repository_id == repository_id,
                SecurityScan.is_active == 1,
            )
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_artifacts(self, repository_id: uuid.UUID) -> list[tuple[Artifact, int]]:
        """Get active artifacts linked to active pipeline runs for a repository.

        Returns:
            List of tuples (Artifact, run_number) sorted by uploaded_at desc.
        """
        stmt = (
            select(Artifact, PipelineRun.run_number)
            .join(PipelineRun, Artifact.pipeline_run_id == PipelineRun.pipeline_run_id)
            .where(
                PipelineRun.repository_id == repository_id,
                PipelineRun.is_active == 1,
                Artifact.is_active == 1,
            )
            .order_by(Artifact.uploaded_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.tuples().all())
