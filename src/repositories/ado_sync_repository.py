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
from src.repositories.schema.specialization import Specialization
from src.repositories.schema.status import Status
from src.utils.helpers import log_error_to_db
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

    async def get_applicable_tickets(self) -> list[DevsecopsTicket]:
        """Get all applicable active devsecops tickets for syncing.

        Returns tickets that are applicable and active, with their
        associated project and specialization information.
        """
        try:
            logger.debug("Inside get_applicable_tickets function")
            stmt = select(DevsecopsTicket).join(
                Project, DevsecopsTicket.project_id == Project.project_id
            ).where(
                Project.is_applicable == True,  # noqa: E712
                Project.is_active == 1,
                DevsecopsTicket.is_active == 1,
            )

            result = await self._session.execute(stmt)
            return list(result.scalars().all())
        except Exception as exc:
            logger.error("Error in get_applicable_tickets", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="get_applicable_tickets",
                error_file="src/repositories/ado_sync_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def get_repositories_for_ticket(self, ticket_id: uuid.UUID) -> list[Repository]:
        """Get active repositories linked to a specific ticket.

        Args:
            ticket_id: The devsecops ticket UUID.

        Returns:
            List of Repository objects linked to the ticket.
        """
        try:
            stmt = select(Repository).where(
                Repository.ticket_id == ticket_id,
                Repository.is_active == 1,
            )
            result = await self._session.execute(stmt)
            return list(result.scalars().all())
        except Exception as exc:
            logger.error("Error in get_repositories_for_ticket", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="get_repositories_for_ticket",
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

    async def upsert_pipeline_runs(self, runs: list[PipelineRun]) -> None:
        """Upsert pipeline run records matched by (repository_id, run_number).

        Existing active records with the same run_number are updated in place.
        New records are inserted. Records not in the incoming list are untouched.
        """
        try:
            now = datetime.utcnow()
            for run in runs:
                stmt = select(PipelineRun).where(
                    PipelineRun.repository_id == run.repository_id,
                    PipelineRun.run_number == run.run_number,
                    PipelineRun.is_active == 1,
                )
                result = await self._session.execute(stmt)
                existing = result.scalar_one_or_none()
                if existing:
                    existing.status = run.status
                    existing.branch = run.branch
                    existing.duration_seconds = run.duration_seconds
                    existing.triggered_at = run.triggered_at
                    existing.modified_at = now
                    existing.modified_by = run.created_by
                else:
                    self._session.add(run)
            await self._session.flush()
        except Exception as exc:
            logger.error("Error in upsert_pipeline_runs", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="upsert_pipeline_runs",
                error_file="src/repositories/ado_sync_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def upsert_commits(self, commits: list[Commit]) -> None:
        """Upsert commit records matched by (repository_id, hash).

        Existing active commits with the same hash are updated in place.
        New commits are inserted. Commits not in the incoming list are untouched.
        """
        try:
            now = datetime.utcnow()
            for commit in commits:
                stmt = select(Commit).where(
                    Commit.repository_id == commit.repository_id,
                    Commit.hash == commit.hash,
                    Commit.is_active == 1,
                )
                result = await self._session.execute(stmt)
                existing = result.scalar_one_or_none()
                if existing:
                    existing.message = commit.message
                    existing.author = commit.author
                    existing.committed_at = commit.committed_at
                    existing.modified_at = now
                    existing.modified_by = commit.created_by
                else:
                    self._session.add(commit)
            await self._session.flush()
        except Exception as exc:
            logger.error("Error in upsert_commits", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="upsert_commits",
                error_file="src/repositories/ado_sync_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def upsert_pull_requests(self, prs: list[PullRequest]) -> None:
        """Upsert pull request records matched by (repository_id, title).

        Existing active PRs with the same title are updated in place.
        New PRs are inserted. PRs not in the incoming list are untouched.
        """
        try:
            now = datetime.utcnow()
            for pr in prs:
                stmt = select(PullRequest).where(
                    PullRequest.repository_id == pr.repository_id,
                    PullRequest.title == pr.title,
                    PullRequest.is_active == 1,
                )
                result = await self._session.execute(stmt)
                existing = result.scalar_one_or_none()
                if existing:
                    existing.author = pr.author
                    existing.status = pr.status
                    existing.updated_at = pr.updated_at
                    existing.modified_at = now
                    existing.modified_by = pr.created_by
                else:
                    self._session.add(pr)
            await self._session.flush()
        except Exception as exc:
            logger.error("Error in upsert_pull_requests", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="upsert_pull_requests",
                error_file="src/repositories/ado_sync_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def upsert_security_scans(self, scans: list[SecurityScan]) -> None:
        """Insert new security scan records.

        Security scans have no natural unique key from ADO, so each sync
        inserts new records. Existing records remain untouched.
        """
        try:
            self._session.add_all(scans)
            await self._session.flush()
        except Exception as exc:
            logger.error("Error in upsert_security_scans", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="upsert_security_scans",
                error_file="src/repositories/ado_sync_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def upsert_artifacts(self, artifacts: list[Artifact]) -> None:
        """Upsert artifact records matched by (pipeline_run_id, artifact_name).

        Existing active artifacts with the same name on the same pipeline run
        are updated in place. New artifacts are inserted. Others are untouched.
        """
        try:
            now = datetime.utcnow()
            for artifact in artifacts:
                stmt = select(Artifact).where(
                    Artifact.pipeline_run_id == artifact.pipeline_run_id,
                    Artifact.artifact_name == artifact.artifact_name,
                    Artifact.is_active == 1,
                )
                result = await self._session.execute(stmt)
                existing = result.scalar_one_or_none()
                if existing:
                    existing.size_bytes = artifact.size_bytes
                    existing.url = artifact.url
                    existing.uploaded_at = artifact.uploaded_at
                    existing.modified_at = now
                    existing.modified_by = artifact.created_by
                else:
                    self._session.add(artifact)
            await self._session.flush()
        except Exception as exc:
            logger.error("Error in upsert_artifacts", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="upsert_artifacts",
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
        repo_status: str | None = None,
    ) -> None:
        """Update repository aggregate metrics and repo_status after sync."""
        try:
            values: dict = {
                "pipeline_runs_count": pipeline_runs_count,
                "success_rate": success_rate,
                "last_run_at": last_run_at,
                "modified_at": datetime.utcnow(),
                "modified_by": "sync_ado_service",
            }
            if repo_status is not None:
                values["repo_status"] = repo_status

            stmt = (
                update(Repository)
                .where(Repository.repository_id == repository_id)
                .values(**values)
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

    async def get_specialization_ids_from_repositories(
        self, repository_ids: list[uuid.UUID]
    ) -> set[uuid.UUID]:
        """Resolve valid specialization UUIDs from repositories' specialization_names CSV column.

        Each repository stores a comma-separated list of specialization names
        (e.g. "FE,DevSecOps"). This method:
        1. Reads the specialization_names CSV from each repository.
        2. Splits and strips each name.
        3. Looks up matching specialization_id from the specializations table by name.
        4. Returns the set of valid specialization UUIDs found.

        Args:
            repository_ids: List of repository UUIDs to read specialization names from.

        Returns:
            Set of valid specialization UUIDs matched by name.
        """
        try:
            if not repository_ids:
                return set()

            # Fetch specialization_names CSV from repositories
            stmt = select(Repository.specialization_names).where(
                Repository.repository_id.in_(repository_ids),
                Repository.is_active == 1,
                Repository.specialization_names.isnot(None),
            )
            result = await self._session.execute(stmt)
            csv_values = result.scalars().all()

            # Parse all specialization names from CSV strings
            candidate_names: set[str] = set()
            for csv in csv_values:
                if not csv:
                    continue
                for part in csv.split(","):
                    name = part.strip()
                    if name:
                        candidate_names.add(name)

            if not candidate_names:
                return set()

            # Look up specialization_id by name (case-insensitive match)
            valid_stmt = select(Specialization.specialization_id).where(
                Specialization.specialization_name.in_(candidate_names),
                Specialization.is_active == 1,
            )
            valid_result = await self._session.execute(valid_stmt)
            return set(valid_result.scalars().all())

        except Exception as exc:
            logger.error("Error in get_specialization_ids_from_repositories", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="get_specialization_ids_from_repositories",
                error_file="src/repositories/ado_sync_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def get_specialization_ids_by_names(
        self, names: set[str]
    ) -> set[uuid.UUID]:
        """Resolve specialization UUIDs from a set of specialization names.

        Args:
            names: Set of specialization name strings to look up.

        Returns:
            Set of matching specialization UUIDs.
        """
        try:
            if not names:
                return set()
            stmt = select(Specialization.specialization_id).where(
                Specialization.specialization_name.in_(names),
                Specialization.is_active == 1,
            )
            result = await self._session.execute(stmt)
            return set(result.scalars().all())
        except Exception as exc:
            logger.error("Error in get_specialization_ids_by_names", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="get_specialization_ids_by_names",
                error_file="src/repositories/ado_sync_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def get_specialization_ids_for_project(self, project_id: uuid.UUID) -> list[uuid.UUID]:
        """Get distinct specialization UUIDs linked to a project via repositories.specialization_names.

        Reads specialization_names CSV from all repositories linked to the project,
        matches against specializations table by name, returns the UUIDs.
        """
        try:
            # Get specialization_names CSV from repositories linked to this project
            name_stmt = (
                select(Repository.specialization_names)
                .join(DevsecopsTicket, Repository.ticket_id == DevsecopsTicket.ticket_id)
                .where(
                    DevsecopsTicket.project_id == project_id,
                    DevsecopsTicket.is_active == 1,
                    Repository.is_active == 1,
                    Repository.specialization_names.isnot(None),
                )
            )
            name_result = await self._session.execute(name_stmt)
            csv_values = name_result.scalars().all()

            # Parse all names from CSV strings
            candidate_names: set[str] = set()
            for csv in csv_values:
                if not csv:
                    continue
                for part in csv.split(","):
                    name = part.strip()
                    if name:
                        candidate_names.add(name)

            if not candidate_names:
                return []

            # Lookup specialization_id by name
            id_stmt = select(Specialization.specialization_id).where(
                Specialization.specialization_name.in_(candidate_names),
                Specialization.is_active == 1,
            )
            id_result = await self._session.execute(id_stmt)
            return list(id_result.scalars().all())
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
        """Get current project counts grouped by status name for a specialization.

        Filters projects whose linked repositories have the specialization name
        (from repositories.specialization_names CSV) matching the given specialization_id.
        """
        try:
            # Resolve specialization name from ID
            spec_name_stmt = select(Specialization.specialization_name).where(
                Specialization.specialization_id == specialization_id,
                Specialization.is_active == 1,
            )
            spec_name_result = await self._session.execute(spec_name_stmt)
            specialization_name = spec_name_result.scalar_one_or_none()

            if not specialization_name:
                return {}

            # Find project_ids linked to repositories that have this specialization name
            # repositories.specialization_names is a CSV like "FE,DevSecOps"
            # Use LIKE to match the name within the CSV
            repo_project_stmt = (
                select(DevsecopsTicket.project_id)
                .join(Repository, Repository.ticket_id == DevsecopsTicket.ticket_id)
                .where(
                    DevsecopsTicket.is_active == 1,
                    DevsecopsTicket.project_id.isnot(None),
                    Repository.is_active == 1,
                    Repository.specialization_names.isnot(None),
                    Repository.specialization_names.like(f"%{specialization_name}%"),
                )
                .distinct()
            )

            stmt = (
                select(Status.status_name, Project.project_id)
                .join(Status, Project.status_id == Status.status_id, isouter=True)
                .where(
                    Project.is_applicable == True,  # noqa: E712
                    Project.is_active == 1,
                    Project.project_id.in_(repo_project_stmt),
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
