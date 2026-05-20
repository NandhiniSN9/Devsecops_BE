"""Request DTOs for ServiceNow sync endpoints."""

from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator


class SyncProjectItemRequest(BaseModel):
    """Single project item in the sync request payload."""

    model_config = ConfigDict(strict=False)

    sn_project_id: str = Field(min_length=1)
    """ServiceNow project identifier (unique key for deduplication)."""

    project_name: str = Field(min_length=1)
    """Name of the project."""

    onboarded_date: date
    """Date when the project was onboarded (YYYY-MM-DD)."""

    project_type: str = Field(min_length=1)
    """Type/category of the project."""

    specialization_name: str | None = None
    """Specialization name associated with the project (optional, for future use)."""

    is_applicable: bool = True
    """Whether the project is applicable for DevSecOps onboarding."""

    client: str | None = None
    """Client name associated with the project."""

    approver: str | None = None
    """Name or email of the approver."""

    @field_validator("sn_project_id", "project_name", "project_type", mode="before")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        """Strip leading/trailing whitespace from string fields."""
        if isinstance(v, str):
            return v.strip()
        return v


class SyncProjectRequest(BaseModel):
    """Request body for POST /api/v1/sync/servicenow/projects."""

    model_config = ConfigDict(strict=False)

    projects: list[SyncProjectItemRequest] = Field(min_length=1)
    """List of project objects to sync from ServiceNow."""


class RepositoryItemRequest(BaseModel):
    """Single repository item within a DevSecOps ticket."""

    model_config = ConfigDict(strict=False)

    ado_repo_name: str = Field(min_length=1)
    """Azure DevOps repository name."""

    ado_repo_id: str | None = None
    """Azure DevOps repository identifier."""

    specialization: list[str] | None = None
    """List of specialization names this repository belongs to."""

    l1_approvers: list[str] | None = None
    """List of L1 approver email addresses for the repository."""

    @field_validator("ado_repo_name", mode="before")
    @classmethod
    def strip_repo_name(cls, v: str) -> str:
        """Strip leading/trailing whitespace from ado_repo_name."""
        if isinstance(v, str):
            return v.strip()
        return v


class SyncDevSecOpsTicketItemRequest(BaseModel):
    """Single DevSecOps ticket item in the sync request payload."""

    model_config = ConfigDict(strict=False, populate_by_name=True)

    sn_project_id: str = Field(min_length=1)
    """ServiceNow project identifier (used for project resolution)."""

    ado_project_id: str | None = None
    """Azure DevOps project identifier."""

    ado_project_name: str = Field(min_length=1)
    """Name of the ADO project the ticket belongs to."""

    project_type: str | None = None
    """Type of the project (client/internal)."""

    client: str | None = None
    """Client name."""

    repositories: list[RepositoryItemRequest] | None = None
    """Repositories associated with the ticket."""

    requested_by: str | None = None
    """Name or email of the person who raised the request."""

    requested_at: datetime | None = None
    """Timestamp when the ticket was requested in ServiceNow."""

    @field_validator("sn_project_id", "ado_project_name", mode="before")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        """Strip leading/trailing whitespace from string fields."""
        if isinstance(v, str):
            return v.strip()
        return v


class SyncDevSecOpsTicketsRequest(BaseModel):
    """Request body for POST /api/v1/sync/servicenow/devsecops-tickets."""

    model_config = ConfigDict(strict=False)

    tickets: list[SyncDevSecOpsTicketItemRequest] = Field(min_length=1)
    """List of DevSecOps tickets to ingest."""
