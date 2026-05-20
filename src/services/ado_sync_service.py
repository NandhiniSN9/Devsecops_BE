"""Service for synchronizing pipeline data from Azure DevOps."""

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
from src.utils.logger import logger

# Service identifier
SYNC_ADO_SERVICE_IDENTIFIER = "sync_ado_service"


class AdoSyncService:
    """Service for ADO data synchronization operations."""

    def __init__(self, repo: AdoSyncRepository, ado_client: AdoClient) -> None:
        """Initialize with repository and ADO client dependencies."""
        self._repo = repo
        self._ado_client = ado_client

    async def sync_ado_data(self) -> str:

        logger.debug("Inside sync_ado_data")
        """Trigger ADO sync for applicable projects.

        Returns:
            Success message string.
        """
        # Create cron job record
        cron_job = await self._repo.create_cron_job(
            created_by=SYNC_ADO_SERVICE_IDENTIFIER,
        )
        await self._repo.commit()
        cron_id = cron_job.cron_id
        logger.debug("Committed the cron job record")
        has_errors = False

        try:
            projects = await self._repo.get_applicable_projects()

            # Pre-extract project info to avoid lazy loading after rollback
            project_info_list = [
                (project.project_id, project.project_name)
                for project in projects
            ]

            for project_id, project_name in project_info_list:
                repositories = await self._repo.get_repositories_for_project(project_id)

                # Pre-extract attributes to avoid lazy loading after rollback
                repo_info_list = [
                    (repo.repository_id, repo.ado_repo_id)
                    for repo in repositories
                ]

                for repo_id, ado_repo_id in repo_info_list:
                    if not ado_repo_id:
                        continue

                    try:
                        # Re-fetch the repository object in a clean session state
                        repository = await self._repo.get_repository_by_id(repo_id)
                        if not repository:
                            continue
                        await self._sync_repository(repository, project_name)
                    except Exception as exc:
                        has_errors = True
                        await self._repo.rollback()
                        logger.error(
                            "Failed to sync repository",
                            repository_id=str(repo_id),
                            ado_repo_id=ado_repo_id,
                            error=str(exc),
                        )

            # Update KPI history only if all syncs passed
            if not has_errors:
                await self._update_kpi_histories(project_info_list)

            # Update cron job status
            final_status = "fail" if has_errors else "success"
            await self._repo.update_cron_job_status(
                cron_id, final_status, SYNC_ADO_SERVICE_IDENTIFIER
            )
            await self._repo.commit()

        except Exception as exc:
            await self._repo.rollback()
            await self._repo.update_cron_job_status(
                cron_id, "fail", SYNC_ADO_SERVICE_IDENTIFIER
            )
            await self._repo.commit()
            raise exc

        return "Sync completed successfully"

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
                    run_number=run.get("buildNumber", 0),
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
        self, project_info_list: list[tuple[uuid.UUID, str]]
    ) -> None:
        """Update KPI history for affected specializations.

        Args:
            project_info_list: List of (project_id, project_name) tuples.
        """
        spec_ids: set[uuid.UUID] = set()

        for project_id, _ in project_info_list:
            project_spec_ids = await self._repo.get_specialization_ids_for_project(project_id)
            spec_ids.update(project_spec_ids)

        for spec_id in spec_ids:
            try:
                await self._create_kpi_snapshot(spec_id)
            except Exception as exc:
                logger.error(
                    "Failed to update KPI history",
                    specialization_id=str(spec_id),
                    error=str(exc),
                )

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
