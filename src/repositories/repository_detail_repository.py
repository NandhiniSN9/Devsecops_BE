"""Repository for repository detail data access operations."""

import asyncio
import traceback
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
from src.utils.logger import logger


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
        try:
            stmt = select(Repository).where(
                Repository.repository_id == repository_id,
                Repository.is_active == 1,
            )
            result = await self._session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as exc:
            logger.error("Error in get_repository_by_id", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="get_repository_by_id",
                error_file="src/repositories/repository_detail_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def get_ticket_for_repository(self, ticket_id: uuid.UUID) -> DevsecopsTicket | None:
        """Get the devsecops ticket linked to a repository."""
        try:
            stmt = select(DevsecopsTicket).where(
                DevsecopsTicket.ticket_id == ticket_id,
                DevsecopsTicket.is_active == 1,
            )
            result = await self._session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as exc:
            logger.error("Error in get_ticket_for_repository", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="get_ticket_for_repository",
                error_file="src/repositories/repository_detail_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def get_project_by_id(self, project_id: uuid.UUID) -> Project | None:
        """Get an active project by ID."""
        try:
            stmt = select(Project).where(
                Project.project_id == project_id,
                Project.is_active == 1,
            )
            result = await self._session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as exc:
            logger.error("Error in get_project_by_id", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="get_project_by_id",
                error_file="src/repositories/repository_detail_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def get_project_by_sn_id(self, sn_project_id: str) -> Project | None:
        """Get an active project by ServiceNow project ID."""
        try:
            stmt = select(Project).where(
                Project.sn_project_id == sn_project_id,
                Project.is_active == 1,
            )
            result = await self._session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as exc:
            logger.error("Error in get_project_by_sn_id", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="get_project_by_sn_id",
                error_file="src/repositories/repository_detail_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def get_at_risk_threshold(self, specialization_id: uuid.UUID) -> int | None:
        """Get the at-risk threshold for a specialization from settings."""
        try:
            stmt = select(Setting.at_risk_threshold).where(
                Setting.specialization_id == specialization_id,
                Setting.is_active == 1,
            )
            result = await self._session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as exc:
            logger.error("Error in get_at_risk_threshold", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="get_at_risk_threshold",
                error_file="src/repositories/repository_detail_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def get_pipeline_runs(self, repository_id: uuid.UUID) -> list[PipelineRun]:
        """Get all active pipeline runs for a repository, sorted by triggered_at desc."""
        try:
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
        except Exception as exc:
            logger.error("Error in get_pipeline_runs", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="get_pipeline_runs",
                error_file="src/repositories/repository_detail_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def get_total_pipeline_runs_count(self, repository_id: uuid.UUID) -> int:
        """Get total count of active pipeline runs for a repository."""
        try:
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
        except Exception as exc:
            logger.error("Error in get_total_pipeline_runs_count", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="get_total_pipeline_runs_count",
                error_file="src/repositories/repository_detail_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def get_last_30_pipeline_runs(self, repository_id: uuid.UUID) -> list[PipelineRun]:
        """Get the last 30 pipeline runs for success rate calculation."""
        try:
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
        except Exception as exc:
            logger.error("Error in get_last_30_pipeline_runs", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="get_last_30_pipeline_runs",
                error_file="src/repositories/repository_detail_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def get_commits(self, repository_id: uuid.UUID) -> list[Commit]:
        """Get all active commits for a repository, sorted by committed_at desc."""
        try:
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
        except Exception as exc:
            logger.error("Error in get_commits", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="get_commits",
                error_file="src/repositories/repository_detail_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def get_pull_requests(self, repository_id: uuid.UUID) -> list[PullRequest]:
        """Get all active pull requests for a repository, sorted by updated_at desc."""
        try:
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
        except Exception as exc:
            logger.error("Error in get_pull_requests", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="get_pull_requests",
                error_file="src/repositories/repository_detail_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def get_security_scans(self, repository_id: uuid.UUID) -> list[SecurityScan]:
        """Get all active security scans for a repository."""
        try:
            stmt = (
                select(SecurityScan)
                .where(
                    SecurityScan.repository_id == repository_id,
                    SecurityScan.is_active == 1,
                )
            )
            result = await self._session.execute(stmt)
            return list(result.scalars().all())
        except Exception as exc:
            logger.error("Error in get_security_scans", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="get_security_scans",
                error_file="src/repositories/repository_detail_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def get_artifacts(self, repository_id: uuid.UUID) -> list[tuple[Artifact, int]]:
        """Get active artifacts linked to active pipeline runs for a repository.

        Returns:
            List of tuples (Artifact, run_number) sorted by uploaded_at desc.
        """
        try:
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
        except Exception as exc:
            logger.error("Error in get_artifacts", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="get_artifacts",
                error_file="src/repositories/repository_detail_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise
