"""Response DTOs for the Repository Detail endpoint."""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class ProjectRefResponse(BaseModel):
    """Parent project reference in repository header."""

    model_config = ConfigDict(strict=False)

    id: uuid.UUID
    """Parent project UUID."""

    name: str
    """Parent project name."""


class RepositoryHeaderResponse(BaseModel):
    """Repository header metadata."""

    model_config = ConfigDict(strict=False)

    id: uuid.UUID
    """Unique identifier for the repository."""

    name: str
    """Name of the repository."""

    overdue: int | None = None
    """Number of days overdue, null if not overdue."""

    client: str | None = None
    """Client name associated with the repository."""

    onboarding_date: date | None = None
    """Date when the repository was onboarded."""

    closed_by: date | None = None
    """Expected completion date or null if not completed."""

    project_type: str | None = None
    """Specialization and category label."""

    project: ProjectRefResponse | None = None
    """Parent project reference."""


class PipelineMetricsResponse(BaseModel):
    """Pipeline metrics for a repository."""

    model_config = ConfigDict(strict=False)

    total_runs: int = 0
    """Total pipeline runs since first connection."""

    success_rate: float = 0.0
    """Success rate percentage from the last 30 pipeline runs."""

    last_pipeline_run: int | None = None
    """Number of days since the last pipeline run."""

    last_pipeline_run_at: datetime | None = None
    """ISO 8601 timestamp of the last pipeline run."""


class AdoptionTimelineStepResponse(BaseModel):
    """Single step in the adoption timeline."""

    model_config = ConfigDict(strict=False)

    step: str
    """Step identifier (kicked_off, pipeline_detected, first_run, adopted)."""

    label: str
    """Human-readable label for the step."""

    status: str
    """Current status (completed, in_progress, pending)."""

    completed_at: date | None = None
    """Completion date or null if not completed."""


class PipelineRunResponse(BaseModel):
    """Single pipeline run record."""

    model_config = ConfigDict(strict=False)

    run_number: int
    """Pipeline run number."""

    status: str
    """Run status (passed, failed, running, cancelled)."""

    branch: str
    """Branch name the pipeline ran on."""

    duration: str
    """Human-readable duration."""

    triggered_at: datetime
    """Timestamp when the pipeline run was triggered."""


class PipelineActivityResponse(BaseModel):
    """Pipeline activity section."""

    model_config = ConfigDict(strict=False)

    runs: list[PipelineRunResponse] = []
    """List of pipeline run records."""


class CommitItemResponse(BaseModel):
    """Single commit record."""

    model_config = ConfigDict(strict=False)

    hash: str
    """Abbreviated commit hash (first 6 characters)."""

    message: str
    """Full commit message."""

    author: str
    """Author name."""

    committed_at: datetime
    """Timestamp of the commit."""


class CommitsResponse(BaseModel):
    """Commits section."""

    model_config = ConfigDict(strict=False)

    commit_details: list[CommitItemResponse] = []
    """List of commit records."""


class PullRequestSummaryResponse(BaseModel):
    """Pull request summary counts."""

    model_config = ConfigDict(strict=False)

    open: int = 0
    """Count of open pull requests."""

    merged: int = 0
    """Count of merged pull requests."""

    declined: int = 0
    """Count of declined pull requests."""


class PullRequestItemResponse(BaseModel):
    """Single pull request record."""

    model_config = ConfigDict(strict=False)

    title: str
    """Pull request title."""

    author: str
    """Author name."""

    status: str
    """PR status (open, merged, declined)."""

    updated_at: datetime | None = None
    """Timestamp of the last update."""


class PullRequestsResponse(BaseModel):
    """Pull requests section."""

    model_config = ConfigDict(strict=False)

    summary: PullRequestSummaryResponse = PullRequestSummaryResponse()
    """Summary counts by status."""

    pull_requests_details: list[PullRequestItemResponse] = []
    """List of pull request records."""


class ScanTypeCountResponse(BaseModel):
    """Count for a single scan type."""

    model_config = ConfigDict(strict=False)

    count: int = 0
    """Number of findings."""


class SecurityScansResponse(BaseModel):
    """Security scans section."""

    model_config = ConfigDict(strict=False)

    total_findings: int = 0
    """Sum of all findings across all scan types."""

    sca: ScanTypeCountResponse = ScanTypeCountResponse()
    """SCA findings."""

    sast: ScanTypeCountResponse = ScanTypeCountResponse()
    """SAST findings."""

    dast: ScanTypeCountResponse = ScanTypeCountResponse()
    """DAST findings."""


class ArtifactItemResponse(BaseModel):
    """Single artifact record."""

    model_config = ConfigDict(strict=False)

    filename: str
    """Name of the artifact file."""

    size_bytes: int
    """File size in bytes."""

    size_label: str
    """Human-readable file size."""

    build_number: int
    """Associated pipeline run number."""

    created_at: datetime
    """Timestamp when the artifact was uploaded."""

    download_url: str
    """URL to download the artifact."""


class ArtifactsResponse(BaseModel):
    """Artifacts section."""

    model_config = ConfigDict(strict=False)

    artifacts_details: list[ArtifactItemResponse] = []
    """List of artifact records."""


class RepositoryDetailDataResponse(BaseModel):
    """Full repository detail response payload."""

    model_config = ConfigDict(strict=False)

    header: RepositoryHeaderResponse
    """Repository header metadata."""

    pipeline_metrics: PipelineMetricsResponse
    """Pipeline metrics."""

    adoption_timeline: list[AdoptionTimelineStepResponse]
    """Ordered list of adoption timeline steps."""

    pipeline_activity: PipelineActivityResponse
    """Pipeline activity section."""

    commits: CommitsResponse
    """Commits section."""

    pull_requests: PullRequestsResponse
    """Pull requests section."""

    security_scans: SecurityScansResponse
    """Security scans section."""

    artifacts: ArtifactsResponse
    """Artifacts section."""
