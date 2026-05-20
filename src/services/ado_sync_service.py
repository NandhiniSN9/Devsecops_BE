"""Service for synchronizing pipeline data from Azure DevOps."""

import asyncio
import uuid
from datetime import datetime

from src.client.ado_client import AdoClient
from src.repositories.ado_sync_repository import AdoSyncRepository
from src.repositories.schema.artifact import Artifact
from src.repositories.schema.commit import Commit
from src.repositories.schema.kpi_history import KpiHistory
from src.repositories.schema.pipeline_run import PipelineRun
from src.repositories.schema.pull_request import PullRequest
from src.repositories.schema.security_scan import SecurityScan
from src.settings import get_settings
from src.utils.logger import logger

# Service identifier
SYNC_ADO_SERVICE_IDENTIFIER = "sync_ado_service"


class AdoSyncService:
    """Service for ADO data synchronization operations.

    Supports parallel repository syncing with configurable concurrency
    controlled by ADO_SYNC_CONCURRENCY env var (default: 5).
    """

    def __init__(self, repo: AdoSyncRepository, ado_client: AdoClient) -> None:
        """Initialize with repository and ADO client dependencies."""
        self._repo = repo
        self._ado_client = ado_client
        self._concurrency = get_settings().ADO_SYNC_CONCURRENCY

    async def initiate_sync(self) -> dict:
        """Check for pending sync and create cron job record.

        Returns:
            Dict with success flag, message, and cron_id if successful.
        """
        logger.debug("Inside initiate_sync")

        # Check if an ADO sync is already running
        if await self._repo.has_pending_azure_cron_job():
            logger.info("ADO sync already in progress, skipping")
            return {
                "success": False,
                "message": "An ADO sync is already running",
            }

        # Create cron job record
        cron_job = await self._repo.create_cron_job(
            created_by=SYNC_ADO_SERVICE_IDENTIFIER,
        )
        await self._repo.commit()
        logger.debug("Committed the cron job record")

        return {
            "success": True,
            "message": "ADO sync initiated successfully",
            "cron_id": cron_job.cron_id,
        }

    async def run_sync(self, cron_id) -> None:
        """Execute the ADO sync process with parallel repository processing.

        Uses asyncio.Semaphore to limit concurrency to ADO_SYNC_CONCURRENCY
        (default: 5 parallel syncs). Each repository sync is independent —
        failures in one don't block others.

        Args:
            cron_id: UUID of the cron job record to track this sync.
        """
        logger.info(
            "Starting background ADO sync",
            cron_id=str(cron_id),
            concurrency=self._concurrency,
        )
        has_errors = False
        semaphore = asyncio.Semaphore(self._concurrency)

        try:
            tickets = await self._repo.get_applicable_tickets()

            # Pre-extract ticket info to avoid lazy loading after rollback
            ticket_info_list = [
                (ticket.ticket_id, ticket.project_name, ticket.specialization_id)
                for ticket in tickets
            ]

            # Collect all (repo_id, ado_repo_id, project_name) tuples
            sync_tasks_data: list[tuple[uuid.UUID, str, str]] = []
            for ticket_id, project_name, _ in ticket_info_list:
                repositories = await self._repo.get_repositories_for_ticket(ticket_id)
                for repo in repositories:
                    if repo.ado_repo_id:
                        sync_tasks_data.append((repo.repository_id, repo.ado_repo_id, project_name))

            logger.info(
                "Repositories to sync",
                total=len(sync_tasks_data),
                concurrency=self._concurrency,
            )

            # Run repository syncs in parallel with semaphore-limited concurrency
            results = await asyncio.gather(
                *[
                    self._sync_repository_with_semaphore(semaphore, repo_id, ado_repo_id, project_name)
                    for repo_id, ado_repo_id, project_name in sync_tasks_data
                ],
                return_exceptions=True,
            )

            # Check results for failures
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    has_errors = True
                    repo_id, ado_repo_id, _ = sync_tasks_data[i]
                    logger.error(
                        "Repository sync failed",
                        repository_id=str(repo_id),
                        ado_repo_id=ado_repo_id,
                        error=str(result),
                    )
                elif result is False:
                    has_errors = True

            # Update KPI history only if all syncs passed
            if not has_errors:
                spec_ids: set[uuid.UUID] = {
                    spec_id
                    for _, _, spec_id in ticket_info_list
                    if spec_id is not None
                }
                await self._update_kpi_histories(spec_ids)

            # Update cron job status
            final_status = "fail" if has_errors else "success"
            await self._repo.update_cron_job_status(
                cron_id, final_status, SYNC_ADO_SERVICE_IDENTIFIER
            )
            await self._repo.commit()

            logger.info(
                "ADO sync completed",
                cron_id=str(cron_id),
                status=final_status,
                total_repos=len(sync_tasks_data),
                failed=sum(1 for r in results if isinstance(r, Exception) or r is False),
            )

        except Exception as exc:
            await self._repo.rollback()
            await self._repo.update_cron_job_status(
                cron_id, "fail", SYNC_ADO_SERVICE_IDENTIFIER
            )
            await self._repo.commit()
            logger.error("ADO sync failed", cron_id=str(cron_id), error=str(exc))

    async def _sync_repository_with_semaphore(
        self,
        semaphore: asyncio.Semaphore,
        repo_id: uuid.UUID,
        ado_repo_id: str,
        project_name: str,
    ) -> bool:
        """Sync a single repository with semaphore-controlled concurrency.

        Args:
            semaphore: Asyncio semaphore limiting parallel executions.
            repo_id: Internal repository UUID.
            ado_repo_id: Azure DevOps repository identifier.
            project_name: ADO project name.

        Returns:
            True if sync succeeded, False if failed.
        """
        async with semaphore:
            try:
                repository = await self._repo.get_repository_by_id(repo_id)
                if not repository:
                    return True  # Skip silently, not a failure
                await self._sync_repository(repository, project_name)
                return True
            except Exception as exc:
                await self._repo.rollback()
                logger.error(
                    "Failed to sync repository",
                    repository_id=str(repo_id),
                    ado_repo_id=ado_repo_id,
                    error=str(exc),
                )
                return False

    async def _sync_repository(self, repository, project_name: str) -> None:
        """Sync all data types for a single repository.

        Args:
            repository: Repository ORM object with ado_repo_id.
            project_name: ADO project name from the database.
        """
        repo_id = repository.repository_id
        ado_repo_id = repository.ado_repo_id

        logger.info("Syncing repository", repository_id=str(repo_id), ado_repo_id=ado_repo_id, project=project_name)

        # Fetch data from ADO
        ado_runs = await self._ado_client.get_pipeline_runs(ado_repo_id, project=project_name)
        ado_commits = await self._ado_client.get_commits(ado_repo_id, project=project_name)
        ado_prs = await self._ado_client.get_pull_requests(ado_repo_id, project=project_name)

        # Soft-delete existing records
        await self._repo.soft_delete_pipeline_runs(repo_id)
        await self._repo.soft_delete_commits(repo_id)
        await self._repo.soft_delete_pull_requests(repo_id)
        await self._repo.soft_delete_security_scans(repo_id)
        await self._repo.soft_delete_artifacts_for_repository(repo_id)

        # Insert new pipeline runs
        pipeline_run_records = []
        for run in ado_runs:
            pipeline_run_records.append(
                PipelineRun(
                    repository_id=repo_id,
                    run_number=run.get("id", 0),
                    status=self._map_build_status(run.get("result", "")),
                    branch=self._strip_branch_prefix(run.get("sourceBranch", "")),
                    duration_seconds=self._compute_duration(run.get("startTime"), run.get("finishTime")),
                    triggered_at=self._parse_datetime(run.get("queueTime")) or datetime.utcnow(),
                    created_by=SYNC_ADO_SERVICE_IDENTIFIER,
                )
            )
        if pipeline_run_records:
            await self._repo.insert_pipeline_runs(pipeline_run_records)

        # Insert new commits
        commit_records = []
        for commit in ado_commits:
            author_info = commit.get("author", {})
            commit_records.append(
                Commit(
                    repository_id=repo_id,
                    hash=commit.get("commitId", ""),
                    message=commit.get("comment", ""),
                    author=author_info.get("name", "Unknown"),
                    committed_at=self._parse_datetime(author_info.get("date")) or datetime.utcnow(),
                    created_by=SYNC_ADO_SERVICE_IDENTIFIER,
                )
            )
        if commit_records:
            await self._repo.insert_commits(commit_records)

        # Insert new pull requests
        pr_records = []
        for pr in ado_prs:
            created_by_info = pr.get("createdBy", {})
            pr_records.append(
                PullRequest(
                    repository_id=repo_id,
                    title=pr.get("title", ""),
                    author=created_by_info.get("displayName", "Unknown"),
                    status=self._map_pr_status(pr.get("status", "")),
                    updated_at=self._parse_datetime(pr.get("closedDate") or pr.get("creationDate")),
                    created_by=SYNC_ADO_SERVICE_IDENTIFIER,
                )
            )
        if pr_records:
            await self._repo.insert_pull_requests(pr_records)

        # Fetch and insert artifacts from the most recent build
        if ado_runs and pipeline_run_records:
            most_recent_build = ado_runs[0]
            build_id = most_recent_build.get("id")
            if build_id:
                ado_artifacts = await self._ado_client.get_build_artifacts(build_id, project=project_name)
                artifact_records = []
                for art in ado_artifacts:
                    resource = art.get("resource", {})
                    artifact_records.append(
                        Artifact(
                            pipeline_run_id=pipeline_run_records[0].pipeline_run_id,
                            artifact_name=art.get("name", "unknown"),
                            size_bytes=resource.get("properties", {}).get("artifactsize", 0),
                            url=resource.get("downloadUrl", ""),
                            uploaded_at=self._parse_datetime(
                                most_recent_build.get("finishTime")
                            ) or datetime.utcnow(),
                            created_by=SYNC_ADO_SERVICE_IDENTIFIER,
                        )
                    )
                if artifact_records:
                    await self._repo.insert_artifacts(artifact_records)

        # Update repository aggregate metrics
        total_runs = repository.pipeline_runs_count or 0
        total_runs += len(pipeline_run_records)
        passed_count = sum(1 for r in pipeline_run_records if r.status == "passed")
        success_rate = round((passed_count / len(pipeline_run_records)) * 100, 1) if pipeline_run_records else 0.0
        last_run_at = pipeline_run_records[0].triggered_at if pipeline_run_records else repository.last_run_at

        await self._repo.update_repository_metrics(
            repository_id=repo_id,
            pipeline_runs_count=total_runs,
            success_rate=success_rate,
            last_run_at=last_run_at,
        )

        await self._repo.commit()
        logger.info("Repository sync completed", repository_id=str(repo_id))

    async def _update_kpi_histories(
        self, spec_ids: set[uuid.UUID]
    ) -> None:
        """Update ticket timestamps and KPI history for affected specializations.

        For each specialization:
        1. Evaluate and update completed_at / at_risk_at on devsecops_tickets
        2. Create a new KPI history snapshot

        Args:
            spec_ids: Set of specialization UUIDs to update.
        """
        for spec_id in spec_ids:
            try:
                await self._update_ticket_timestamps(spec_id)
                await self._create_kpi_snapshot(spec_id)
            except Exception as exc:
                logger.error(
                    "Failed to update KPI history",
                    specialization_id=str(spec_id),
                    error=str(exc),
                )

    async def _update_ticket_timestamps(self, specialization_id: uuid.UUID) -> None:
        """Evaluate and update completed_at and at_risk_at on devsecops_tickets.

        Logic:
        - completed_at: Set when project status is "Completed" and ticket has no completed_at yet.
                        Cleared (NULL) if project is no longer Completed.
        - at_risk_at:   Set when project exceeds at_risk_threshold days since onboarding
                        without pipeline activity, and ticket has no at_risk_at yet.
                        Cleared (NULL) if project is no longer at risk.

        Args:
            specialization_id: The specialization to evaluate.
        """
        tickets = await self._repo.get_tickets_for_specialization(specialization_id)
        settings = await self._repo.get_settings_for_specialization(specialization_id)
        at_risk_threshold = settings.at_risk_threshold if settings else 10

        now = datetime.utcnow()

        for ticket in tickets:
            project = await self._repo.get_project_by_id(ticket.project_id) if ticket.project_id else None
            if not project:
                continue

            status_name = await self._repo.get_status_name(project.status_id) if project.status_id else None

            # --- completed_at logic ---
            if status_name == "Completed":
                if ticket.completed_at is None:
                    ticket.completed_at = now
                    ticket.modified_at = now
                    ticket.modified_by = SYNC_ADO_SERVICE_IDENTIFIER
            else:
                if ticket.completed_at is not None:
                    ticket.completed_at = None
                    ticket.modified_at = now
                    ticket.modified_by = SYNC_ADO_SERVICE_IDENTIFIER

            # --- at_risk_at logic ---
            if status_name == "At Risk":
                if ticket.at_risk_at is None:
                    ticket.at_risk_at = now
                    ticket.modified_at = now
                    ticket.modified_by = SYNC_ADO_SERVICE_IDENTIFIER
            else:
                if ticket.at_risk_at is not None:
                    ticket.at_risk_at = None
                    ticket.modified_at = now
                    ticket.modified_by = SYNC_ADO_SERVICE_IDENTIFIER

        await self._repo.commit()

    async def _create_kpi_snapshot(self, specialization_id: uuid.UUID) -> None:
        """Create a new KPI history snapshot for a specialization."""
        counts = await self._repo.get_project_counts_by_status(specialization_id)
        previous = await self._repo.get_latest_kpi_history(specialization_id)

        projects_count = sum(counts.values())
        completed_count = counts.get("Completed", 0)
        inactive_count = counts.get("Inactive", 0)
        at_risk_count = counts.get("At Risk", 0)
        not_applicable_count = counts.get("Not Applicable", 0)

        # Calculate deltas
        prev_projects = previous.projects_count if previous else 0
        prev_completed = previous.completed_count if previous else 0
        prev_inactive = previous.inactive_count if previous else 0
        prev_at_risk = previous.at_risk_count if previous else 0
        prev_not_applicable = previous.not_applicable_count if previous else 0

        kpi = KpiHistory(
            specialization_id=specialization_id,
            projects_count=projects_count,
            projects_increase_count=max(projects_count - prev_projects, 0),
            projects_decrease_count=max(prev_projects - projects_count, 0),
            completed_count=completed_count,
            completed_increase_count=max(completed_count - prev_completed, 0),
            completed_decrease_count=max(prev_completed - completed_count, 0),
            inactive_count=inactive_count,
            inactive_increase_count=max(inactive_count - prev_inactive, 0),
            inactive_decrease_count=max(prev_inactive - inactive_count, 0),
            at_risk_count=at_risk_count,
            at_risk_increase_count=max(at_risk_count - prev_at_risk, 0),
            at_risk_decrease_count=max(prev_at_risk - at_risk_count, 0),
            not_applicable_count=not_applicable_count,
            not_applicable_increase_count=max(not_applicable_count - prev_not_applicable, 0),
            not_applicable_decrease_count=max(prev_not_applicable - not_applicable_count, 0),
            created_by=SYNC_ADO_SERVICE_IDENTIFIER,
        )

        await self._repo.insert_kpi_history(kpi)

    @staticmethod
    def _map_build_status(result: str) -> str:
        """Map ADO build result to internal status."""
        mapping = {
            "succeeded": "passed",
            "failed": "failed",
            "canceled": "cancelled",
            "partiallySucceeded": "passed",
        }
        return mapping.get(result, "running")

    @staticmethod
    def _map_pr_status(status: str) -> str:
        """Map ADO PR status to internal status."""
        mapping = {
            "active": "open",
            "completed": "merged",
            "abandoned": "declined",
        }
        return mapping.get(status, "open")

    @staticmethod
    def _strip_branch_prefix(branch: str) -> str:
        """Strip refs/heads/ prefix from branch name."""
        if branch.startswith("refs/heads/"):
            return branch[len("refs/heads/"):]
        return branch

    @staticmethod
    def _compute_duration(start_time: str | None, finish_time: str | None) -> int | None:
        """Compute duration in seconds between start and finish times."""
        if not start_time or not finish_time:
            return None
        try:
            start = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
            finish = datetime.fromisoformat(finish_time.replace("Z", "+00:00"))
            return max(int((finish - start).total_seconds()), 0)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _parse_datetime(value: str | None) -> datetime | None:
        """Parse an ISO 8601 datetime string, returning a naive UTC datetime."""
        if not value:
            return None
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
            # Strip timezone info for naive TIMESTAMP columns
            return dt.replace(tzinfo=None)
        except (ValueError, TypeError):
            return None
