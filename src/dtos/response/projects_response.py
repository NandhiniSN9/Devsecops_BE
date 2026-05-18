"""Response DTOs for the Projects endpoint."""

import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class NotApplicableDetailsResponse(BaseModel):
    """Jira ticket details for a project marked as Not Applicable."""

    model_config = ConfigDict(strict=False)

    reason_category: str | None = None
    """Category of the reason for marking the project as not applicable."""

    comments: str | None = None
    """Comments explaining why the project was marked as not applicable."""

    evidence_url: str | None = None
    """URL to the evidence file uploaded when marking the project."""

    type: str | None = None
    """Type of the Jira ticket."""

    priority: str | None = None
    """Priority level of the Jira ticket."""

    assignee: str | None = None
    """Person assigned to the Jira ticket."""

    jira_status: str | None = None
    """Current status of the Jira ticket."""


class RepositoryItemResponse(BaseModel):
    """Repository item within a project's repositories list."""

    model_config = ConfigDict(strict=False)

    id: uuid.UUID
    """Unique identifier for the repository."""

    name: str
    """Name of the repository."""

    onboarded_date: date | None = None
    """Date when the repository was onboarded."""

    status: str | None = None
    """Current status of the repository (PASSED/FAILED)."""


class ProjectItemResponse(BaseModel):
    """Single project item in the projects list response."""

    model_config = ConfigDict(strict=False)

    id: uuid.UUID
    """Unique identifier for the project."""

    name: str
    """Name of the project."""

    onboarded_date: date
    """Date when the project was onboarded."""

    repository_count: int = Field(ge=0)
    """Number of repositories under this project."""

    status: str
    """Current status of the project."""

    at_risk_overdue: int = 0
    """Number of days the project is overdue (0 if not at risk)."""

    repositories: list[RepositoryItemResponse] = []
    """List of repositories under this project."""

    not_applicable_details: NotApplicableDetailsResponse | None = None
    """Jira ticket details when project status is 'Not Applicable', null otherwise."""


class PaginationResponse(BaseModel):
    """Pagination metadata for list responses."""

    model_config = ConfigDict(strict=False)

    offset: int = Field(ge=0)
    """Number of items skipped."""

    limit: int = Field(ge=1)
    """Items per page."""

    total_items: int = Field(ge=0)
    """Total number of items matching the filters."""


class ProjectsListDataResponse(BaseModel):
    """Combined projects list response payload."""

    model_config = ConfigDict(strict=False)

    projects: list[ProjectItemResponse]
    """List of project items for the current page."""

    pagination: PaginationResponse
    """Pagination metadata."""
