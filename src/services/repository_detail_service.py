"""Service for retrieving comprehensive repository detail information."""

import asyncio
import traceback
import uuid
from datetime import datetime

from src.models.response.repository_detail_response import (
    AdoptionTimelineStepResponse,
    ArtifactItemResponse,
    ArtifactsResponse,
    CommitItemResponse,
    CommitsResponse,
    PipelineActivityResponse,
    PipelineMetricsResponse,
    PipelineRunResponse,
    ProjectRefResponse,
    PullRequestItemResponse,
    PullRequestsResponse,
    PullRequestSummaryResponse,
    RepositoryDetailDataResponse,
    RepositoryHeaderResponse,
    ScanTypeCountResponse,
    SecurityScansResponse,
)
from src.repositories.repository_detail_repository import RepositoryDetailRepository
from src.utils.exceptions import InvalidParameterError, NotFoundError
from src.utils.logger import logger

# Service identifier for error logging
REPOSITORIES_SERVICE_IDENTIFIER = "repositories_service"


class RepositoryDetailService:
    """Service for repository detail retrieval operations."""

    def __init__(self, repo: RepositoryDetailRepository) -> None:
        """Initialize with repository dependency."""
        self._repo = repo

    async def get_repository_detail(self, repository_id_str: str) -> RepositoryDetailDataResponse:
        """Retrieve comprehensive detail for a repository.

        Args:
            repository_id_str: UUID string from path parameter.

        Returns:
            RepositoryDetailDataResponse with all sections.

        Raises:
            InvalidParameterError: If UUID format is invalid.
            NotFoundError: If repository not found.
        """
        try:
            repository_id = self._validate_uuid(repository_id_str, "repository_id")

            repository = await self._repo.get_repository_by_id(repository_id)
            if not repository:
                raise NotFoundError("Repository not found")

            # Resolve parent project
            header = await self._build_header(repository)
            pipeline_metrics = await self._build_pipeline_metrics(repository_id)
            adoption_timeline = await self._build_adoption_timeline(repository)
            pipeline_activity = await self._build_pipeline_activity(repository_id)
            commits = await self._build_commits(repository_id)
            pull_requests = await self._build_pull_requests(repository_id)
            security_scans = await self._build_security_scans(repository_id)
            artifacts = await self._build_artifacts(repository_id)

            return RepositoryDetailDataResponse(
                header=header,
                pipeline_metrics=pipeline_metrics,
                adoption_timeline=adoption_timeline,
                pipeline_activity=pipeline_activity,
                commits=commits,
                pull_requests=pull_requests,
                security_scans=security_scans,
                artifacts=artifacts,
            )
        except (InvalidParameterError, NotFoundError):
            raise
        except Exception as exc:
            logger.error("Error in get_repository_detail", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="get_repository_detail",
                error_file="src/services/repository_detail_service.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def _build_header(self, repository) -> RepositoryHeaderResponse:
        """Build the repository header section."""
        try:
            ticket = None
            project = None
            project_ref = None
            client = None
            onboarding_date = None
            closed_by = None
            project_type_str = None
            overdue = None

            if repository.ticket_id:
                ticket = await self._repo.get_ticket_for_repository(repository.ticket_id)

            if ticket:
                # Resolve project
                if ticket.project_id:
                    project = await self._repo.get_project_by_id(ticket.project_id)
                elif ticket.sn_project_id:
                    project = await self._repo.get_project_by_sn_id(ticket.sn_project_id)

                onboarding_date = (
                    ticket.requested_at.date() if ticket.requested_at else
                    (repository.created_at.date() if repository.created_at else None)
                )

            if project:
                project_ref = ProjectRefResponse(id=project.project_id, name=project.project_name)
                client = project.client
                closed_by = project.completed_at.date() if project.completed_at else None

                # Build project_type string
                spec_name = project.specialization_name or ""
                p_type = project.project_type or ""
                if spec_name and p_type:
                    project_type_str = f"{spec_name} · {p_type}"
                else:
                    project_type_str = spec_name or p_type or None

                # Calculate overdue
                if ticket and ticket.specialization_id and onboarding_date:
                    threshold = await self._repo.get_at_risk_threshold(ticket.specialization_id)
                    if threshold:
                        days_since = (datetime.utcnow().date() - onboarding_date).days
                        if days_since > threshold:
                            overdue = days_since - threshold

            return RepositoryHeaderResponse(
                id=repository.repository_id,
                name=repository.repository_name,
                overdue=overdue,
                client=client,
                onboarding_date=onboarding_date,
                closed_by=closed_by,
                project_type=project_type_str,
                project=project_ref,
            )
        except Exception as exc:
            logger.error("Error in _build_header", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="_build_header",
                error_file="src/services/repository_detail_service.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def _build_pipeline_metrics(self, repository_id: uuid.UUID) -> PipelineMetricsResponse:
        """Build the pipeline metrics section."""
        try:
            total_runs = await self._repo.get_total_pipeline_runs_count(repository_id)
            last_30 = await self._repo.get_last_30_pipeline_runs(repository_id)

            success_rate = 0.0
            if last_30:
                passed_count = sum(1 for r in last_30 if r.status == "passed")
                success_rate = round((passed_count / len(last_30)) * 100, 1)

            last_pipeline_run = None
            last_pipeline_run_at = None
            if last_30:
                most_recent = last_30[0]
                last_pipeline_run_at = most_recent.triggered_at
                days_since = (datetime.utcnow() - most_recent.triggered_at).days
                last_pipeline_run = days_since

            return PipelineMetricsResponse(
                total_runs=total_runs,
                success_rate=success_rate,
                last_pipeline_run=last_pipeline_run,
                last_pipeline_run_at=last_pipeline_run_at,
            )
        except Exception as exc:
            logger.error("Error in _build_pipeline_metrics", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="_build_pipeline_metrics",
                error_file="src/services/repository_detail_service.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def _build_adoption_timeline(self, repository) -> list[AdoptionTimelineStepResponse]:
        """Build the adoption timeline section."""
        try:
            pipeline_runs = await self._repo.get_pipeline_runs(repository.repository_id)

            # Step 1: kicked_off — always completed for existing repositories
            onboarding_date = repository.created_at.date() if repository.created_at else None
            kicked_off = AdoptionTimelineStepResponse(
                step="kicked_off",
                label="Kicked Off",
                status="completed",
                completed_at=onboarding_date,
            )

            # Step 2: pipeline_detected
            if pipeline_runs:
                earliest_run = pipeline_runs[-1]  # sorted desc, last is earliest
                pipeline_detected = AdoptionTimelineStepResponse(
                    step="pipeline_detected",
                    label="Pipeline Detected",
                    status="completed",
                    completed_at=earliest_run.triggered_at.date() if earliest_run.triggered_at else None,
                )
            else:
                pipeline_detected = AdoptionTimelineStepResponse(
                    step="pipeline_detected",
                    label="Pipeline Detected",
                    status="in_progress",
                    completed_at=None,
                )

            # Step 3: first_run — first successful run
            passed_runs = [r for r in pipeline_runs if r.status == "passed"]
            if passed_runs:
                earliest_passed = passed_runs[-1]
                first_run = AdoptionTimelineStepResponse(
                    step="first_run",
                    label="First Run",
                    status="completed",
                    completed_at=earliest_passed.triggered_at.date() if earliest_passed.triggered_at else None,
                )
            elif pipeline_runs:
                first_run = AdoptionTimelineStepResponse(
                    step="first_run",
                    label="First Run",
                    status="in_progress",
                    completed_at=None,
                )
            else:
                first_run = AdoptionTimelineStepResponse(
                    step="first_run",
                    label="First Run",
                    status="pending",
                    completed_at=None,
                )

            # Step 4: adopted — multiple successful runs
            if len(passed_runs) >= 3:
                adopted = AdoptionTimelineStepResponse(
                    step="adopted",
                    label="Adopted",
                    status="completed",
                    completed_at=passed_runs[0].triggered_at.date() if passed_runs[0].triggered_at else None,
                )
            else:
                adopted = AdoptionTimelineStepResponse(
                    step="adopted",
                    label="Adopted",
                    status="pending",
                    completed_at=None,
                )

            return [kicked_off, pipeline_detected, first_run, adopted]
        except Exception as exc:
            logger.error("Error in _build_adoption_timeline", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="_build_adoption_timeline",
                error_file="src/services/repository_detail_service.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def _build_pipeline_activity(self, repository_id: uuid.UUID) -> PipelineActivityResponse:
        """Build the pipeline activity section."""
        try:
            runs = await self._repo.get_pipeline_runs(repository_id)

            run_items = [
                PipelineRunResponse(
                    run_number=r.run_number,
                    status=r.status,
                    branch=r.branch,
                    duration=self._format_duration(r.duration_seconds),
                    triggered_at=r.triggered_at,
                )
                for r in runs
            ]

            return PipelineActivityResponse(runs=run_items)
        except Exception as exc:
            logger.error("Error in _build_pipeline_activity", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="_build_pipeline_activity",
                error_file="src/services/repository_detail_service.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def _build_commits(self, repository_id: uuid.UUID) -> CommitsResponse:
        """Build the commits section."""
        try:
            commits = await self._repo.get_commits(repository_id)

            commit_items = [
                CommitItemResponse(
                    hash=c.hash[:6],
                    message=c.message,
                    author=c.author,
                    committed_at=c.committed_at,
                )
                for c in commits
            ]

            return CommitsResponse(commit_details=commit_items)
        except Exception as exc:
            logger.error("Error in _build_commits", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="_build_commits",
                error_file="src/services/repository_detail_service.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def _build_pull_requests(self, repository_id: uuid.UUID) -> PullRequestsResponse:
        """Build the pull requests section."""
        try:
            prs = await self._repo.get_pull_requests(repository_id)

            summary = PullRequestSummaryResponse(
                open=sum(1 for p in prs if p.status == "open"),
                merged=sum(1 for p in prs if p.status == "merged"),
                declined=sum(1 for p in prs if p.status == "declined"),
            )

            pr_items = [
                PullRequestItemResponse(
                    title=p.title,
                    author=p.author,
                    status=p.status,
                    updated_at=p.updated_at,
                )
                for p in prs
            ]

            return PullRequestsResponse(summary=summary, pull_requests_details=pr_items)
        except Exception as exc:
            logger.error("Error in _build_pull_requests", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="_build_pull_requests",
                error_file="src/services/repository_detail_service.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def _build_security_scans(self, repository_id: uuid.UUID) -> SecurityScansResponse:
        """Build the security scans section."""
        try:
            scans = await self._repo.get_security_scans(repository_id)

            sca_count = sum(s.findings_count for s in scans if s.scan_type == "SCA")
            sast_count = sum(s.findings_count for s in scans if s.scan_type == "SAST")
            dast_count = sum(s.findings_count for s in scans if s.scan_type == "DAST")

            return SecurityScansResponse(
                total_findings=sca_count + sast_count + dast_count,
                sca=ScanTypeCountResponse(count=sca_count),
                sast=ScanTypeCountResponse(count=sast_count),
                dast=ScanTypeCountResponse(count=dast_count),
            )
        except Exception as exc:
            logger.error("Error in _build_security_scans", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="_build_security_scans",
                error_file="src/services/repository_detail_service.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def _build_artifacts(self, repository_id: uuid.UUID) -> ArtifactsResponse:
        """Build the artifacts section."""
        try:
            artifact_tuples = await self._repo.get_artifacts(repository_id)

            artifact_items = [
                ArtifactItemResponse(
                    filename=artifact.artifact_name,
                    size_bytes=artifact.size_bytes,
                    size_label=self._format_file_size(artifact.size_bytes),
                    build_number=run_number,
                    created_at=artifact.uploaded_at,
                    download_url=artifact.url,
                )
                for artifact, run_number in artifact_tuples
            ]

            return ArtifactsResponse(artifacts_details=artifact_items)
        except Exception as exc:
            logger.error("Error in _build_artifacts", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="_build_artifacts",
                error_file="src/services/repository_detail_service.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    @staticmethod
    def _validate_uuid(value: str, field_name: str) -> uuid.UUID:
        """Validate and parse a UUID string."""
        try:
            return uuid.UUID(value)
        except (ValueError, AttributeError):
            raise InvalidParameterError(f"Invalid parameter: '{field_name}' must be a valid UUID")

    @staticmethod
    def _format_duration(seconds: int | None) -> str:
        """Format duration_seconds into human-readable string."""
        if seconds is None or seconds <= 0:
            return "0s"
        if seconds < 60:
            return f"{seconds}s"
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        if minutes < 60:
            if remaining_seconds:
                return f"{minutes}m {remaining_seconds}s"
            return f"{minutes}m"
        hours = minutes // 60
        remaining_minutes = minutes % 60
        if remaining_minutes:
            return f"{hours}h {remaining_minutes}m"
        return f"{hours}h"

    @staticmethod
    def _format_file_size(size_bytes: int) -> str:
        """Format bytes into human-readable file size."""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
