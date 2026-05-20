"""Repository for ADO sync data access operations."""

import asyncio
import traceback
import uuid
from datetime import datetime
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
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
from src.repositories.schema.status import Status
from src.utils.logger import logger

class AdoSyncRepository:
    """Data access layer for ADO sync operations."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def has_pending_azure_cron_job(self) -> bool:
        """Check if any cron job with type 'azure' is in 'pending' status."""
        try:
            stmt = select(CronJob).where(
                CronJob.type == "azure",
                CronJob.sync_status == "pending",
                CronJob.is_active == 1,
            )
            result = await self._session.execute(stmt)
            return result.scalar_one_or_none() is not None
        except Exception as exc:
            logger.error("Error in has_pending_azure_cron_job", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="has_pending_azure_cron_job",
                error_file="src/repositories/ado_sync_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def create_cron_job(
        self, created_by: str
    ) -> CronJob:
        """Create a new cron job record with pending status."""
        try:
            cron_job = CronJob(
                type="azure",
                sync_status="pending",
                created_by=created_by,
            )
            self._session.add(cron_job)
            await self._session.flush()
            return cron_job
        except Exception as exc:
            logger.error("Error in create_cron_job", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="create_cron_job",
                error_file="src/repositories/ado_sync_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def update_cron_job_status(
        self, cron_id: uuid.UUID, status: str, modified_by: str
    ) -> None:
        """Update cron job sync_status and modified_at."""
        try:
            stmt = (
                update(CronJob)
                .where(CronJob.cron_id == cron_id)
                .values(
                    sync_status=status,
                    modified_at=datetime.utcnow(),
                    modified_by=modified_by,
                )
            )
            await self._session.execute(stmt)
        except Exception as exc:
            logger.error("Error in update_cron_job_status", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="update_cron_job_status",
                error_file="src/repositories/ado_sync_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def get_applicable_projects(self) -> list[Project]:
        """Get applicable active projects."""
        try:
            logger.debug("Inside get_applicable_projects function")
            stmt = select(Project).where(
                Project.is_applicable == True,  # noqa: E712
                Project.is_active == 1,
            ).limit(5)  # TODO: Remove limit after testing

            result = await self._session.execute(stmt)
            return list(result.scalars().all())
        except Exception as exc:
            logger.error("Error in get_applicable_projects", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="get_applicable_projects",
                error_file="src/repositories/ado_sync_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def get_repositories_for_project(self, project_id: uuid.UUID) -> list[Repository]:
        """Get active repositories linked to a project through devsecops_tickets."""
        try:
            stmt = (
                select(Repository)
                .join(DevsecopsTicket, Repository.ticket_id == DevsecopsTicket.ticket_id)
                .where(
                    DevsecopsTicket.project_id == project_id,
                    DevsecopsTicket.is_active == 1,
                    Repository.is_active == 1,
                )
            )
            result = await self._session.execute(stmt)
            return list(result.scalars().all())
        except Exception as exc:
            logger.error("Error in get_repositories_for_project", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="get_repositories_for_project",
                error_file="src/repositories/ado_sync_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def get_repository_by_id(self, repository_id: uuid.UUID) -> Repository | None:
        """Get a single repository by its ID."""
        try:
            stmt = select(Repository).where(Repository.repository_id == repository_id)
            result = await self._session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as exc:
            logger.error("Error in get_repository_by_id", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="get_repository_by_id",
                error_file="src/repositories/ado_sync_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def soft_delete_pipeline_runs(self, repository_id: uuid.UUID) -> None:
        """Soft-delete all active pipeline runs for a repository."""
        try:
            stmt = (
                update(PipelineRun)
                .where(
                    PipelineRun.repository_id == repository_id,
                    PipelineRun.is_active == 1,
                )
                .values(is_active=0, modified_at=datetime.utcnow())
            )
            await self._session.execute(stmt)
        except Exception as exc:
            logger.error("Error in soft_delete_pipeline_runs", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="soft_delete_pipeline_runs",
                error_file="src/repositories/ado_sync_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def soft_delete_commits(self, repository_id: uuid.UUID) -> None:
        """Soft-delete all active commits for a repository."""
        try:
            stmt = (
                update(Commit)
                .where(
                    Commit.repository_id == repository_id,
                    Commit.is_active == 1,
                )
                .values(is_active=0, modified_at=datetime.utcnow())
            )
            await self._session.execute(stmt)
        except Exception as exc:
            logger.error("Error in soft_delete_commits", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="soft_delete_commits",
                error_file="src/repositories/ado_sync_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def soft_delete_pull_requests(self, repository_id: uuid.UUID) -> None:
        """Soft-delete all active pull requests for a repository."""
        try:
            stmt = (
                update(PullRequest)
                .where(
                    PullRequest.repository_id == repository_id,
                    PullRequest.is_active == 1,
                )
                .values(is_active=0, modified_at=datetime.utcnow())
            )
            await self._session.execute(stmt)
        except Exception as exc:
            logger.error("Error in soft_delete_pull_requests", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="soft_delete_pull_requests",
                error_file="src/repositories/ado_sync_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def soft_delete_security_scans(self, repository_id: uuid.UUID) -> None:
        """Soft-delete all active security scans for a repository."""
        try:
            stmt = (
                update(SecurityScan)
                .where(
                    SecurityScan.repository_id == repository_id,
                    SecurityScan.is_active == 1,
                )
                .values(is_active=0, modified_at=datetime.utcnow())
            )
            await self._session.execute(stmt)
        except Exception as exc:
            logger.error("Error in soft_delete_security_scans", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="soft_delete_security_scans",
                error_file="src/repositories/ado_sync_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def soft_delete_artifacts_for_repository(self, repository_id: uuid.UUID) -> None:
        """Soft-delete all active artifacts linked to a repository's pipeline runs."""
        try:
            pipeline_run_ids = select(PipelineRun.pipeline_run_id).where(
                PipelineRun.repository_id == repository_id,
                PipelineRun.is_active == 1,
            )
            stmt = (
                update(Artifact)
                .where(
                    Artifact.pipeline_run_id.in_(pipeline_run_ids),
                    Artifact.is_active == 1,
                )
                .values(is_active=0, modified_at=datetime.utcnow())
            )
            await self._session.execute(stmt)
        except Exception as exc:
            logger.error("Error in soft_delete_artifacts_for_repository", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="soft_delete_artifacts_for_repository",
                error_file="src/repositories/ado_sync_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def insert_pipeline_runs(self, runs: list[PipelineRun]) -> None:
        """Bulk insert pipeline run records."""
        try:
            self._session.add_all(runs)
            await self._session.flush()
        except Exception as exc:
            logger.error("Error in insert_pipeline_runs", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="insert_pipeline_runs",
                error_file="src/repositories/ado_sync_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def insert_commits(self, commits: list[Commit]) -> None:
        """Bulk insert commit records."""
        try:
            self._session.add_all(commits)
            await self._session.flush()
        except Exception as exc:
            logger.error("Error in insert_commits", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="insert_commits",
                error_file="src/repositories/ado_sync_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def insert_pull_requests(self, prs: list[PullRequest]) -> None:
        """Bulk insert pull request records."""
        try:
            self._session.add_all(prs)
            await self._session.flush()
        except Exception as exc:
            logger.error("Error in insert_pull_requests", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="insert_pull_requests",
                error_file="src/repositories/ado_sync_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def insert_security_scans(self, scans: list[SecurityScan]) -> None:
        """Bulk insert security scan records."""
        try:
            self._session.add_all(scans)
            await self._session.flush()
        except Exception as exc:
            logger.error("Error in insert_security_scans", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="insert_security_scans",
                error_file="src/repositories/ado_sync_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def insert_artifacts(self, artifacts: list[Artifact]) -> None:
        """Bulk insert artifact records."""
        try:
            self._session.add_all(artifacts)
            await self._session.flush()
        except Exception as exc:
            logger.error("Error in insert_artifacts", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="insert_artifacts",
                error_file="src/repositories/ado_sync_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def update_repository_metrics(
        self,
        repository_id: uuid.UUID,
        pipeline_runs_count: int,
        success_rate: float,
        last_run_at: datetime | None,
    ) -> None:
        """Update repository aggregate metrics after sync."""
        try:
            stmt = (
                update(Repository)
                .where(Repository.repository_id == repository_id)
                .values(
                    pipeline_runs_count=pipeline_runs_count,
                    success_rate=success_rate,
                    last_run_at=last_run_at,
                    modified_at=datetime.utcnow(),
                    modified_by="sync_ado_service",
                )
            )
            await self._session.execute(stmt)
        except Exception as exc:
            logger.error("Error in update_repository_metrics", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="update_repository_metrics",
                error_file="src/repositories/ado_sync_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def get_specialization_ids_for_project(self, project_id: uuid.UUID) -> list[uuid.UUID]:
        """Get distinct specialization IDs linked to a project."""
        try:
            stmt = (
                select(DevsecopsTicket.specialization_id)
                .where(
                    DevsecopsTicket.project_id == project_id,
                    DevsecopsTicket.is_active == 1,
                    DevsecopsTicket.specialization_id.isnot(None),
                )
                .distinct()
            )
            result = await self._session.execute(stmt)
            return list(result.scalars().all())
        except Exception as exc:
            logger.error("Error in get_specialization_ids_for_project", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="get_specialization_ids_for_project",
                error_file="src/repositories/ado_sync_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def get_project_counts_by_status(
        self, specialization_id: uuid.UUID
    ) -> dict[str, int]:
        """Get current project counts grouped by status name for a specialization."""
        try:
            stmt = (
                select(Status.status_name, Project.project_id)
                .join(Status, Project.status_id == Status.status_id, isouter=True)
                .where(
                    Project.is_applicable == True,  # noqa: E712
                    Project.is_active == 1,
                    Project.project_id.in_(
                        select(DevsecopsTicket.project_id).where(
                            DevsecopsTicket.specialization_id == specialization_id,
                            DevsecopsTicket.is_active == 1,
                            DevsecopsTicket.project_id.isnot(None),
                        )
                    ),
                )
            )
            result = await self._session.execute(stmt)
            rows = result.all()

            counts: dict[str, int] = {}
            for status_name, _ in rows:
                key = status_name or "Unknown"
                counts[key] = counts.get(key, 0) + 1
            return counts
        except Exception as exc:
            logger.error("Error in get_project_counts_by_status", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="get_project_counts_by_status",
                error_file="src/repositories/ado_sync_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def get_latest_kpi_history(self, specialization_id: uuid.UUID) -> KpiHistory | None:
        """Get the most recent KPI history record for a specialization."""
        try:
            stmt = (
                select(KpiHistory)
                .where(
                    KpiHistory.specialization_id == specialization_id,
                    KpiHistory.is_active == 1,
                )
                .order_by(KpiHistory.created_at.desc())
                .limit(1)
            )
            result = await self._session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as exc:
            logger.error("Error in get_latest_kpi_history", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="get_latest_kpi_history",
                error_file="src/repositories/ado_sync_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def insert_kpi_history(self, kpi: KpiHistory) -> None:
        """Insert a new KPI history record."""
        try:
            self._session.add(kpi)
            await self._session.flush()
        except Exception as exc:
            logger.error("Error in insert_kpi_history", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="insert_kpi_history",
                error_file="src/repositories/ado_sync_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def commit(self) -> None:
        """Commit the current transaction."""
        try:
            await self._session.commit()
        except Exception as exc:
            logger.error("Error in commit", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="commit",
                error_file="src/repositories/ado_sync_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def rollback(self) -> None:
        """Rollback the current transaction."""
        try:
            await self._session.rollback()
        except Exception as exc:
            logger.error("Error in rollback", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="rollback",
                error_file="src/repositories/ado_sync_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise
