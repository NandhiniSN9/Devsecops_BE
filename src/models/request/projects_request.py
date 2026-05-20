"""Request DTOs for the Projects endpoint query parameters and action body."""

from enum import StrEnum
from pydantic import BaseModel, ConfigDict, model_validator


class ProjectPeriodEnum(StrEnum):
    """Valid period filter values for projects endpoint."""

    LAST_WEEK = "last_week"
    LAST_MONTH = "last_month"
    LAST_3_MONTHS = "last_3_months"
    LAST_6_MONTHS = "last_6_months"
    LAST_YEAR = "last_year"


class ProjectSortByEnum(StrEnum):
    """Valid sort_by values for projects endpoint."""

    PROJECT = "project"
    ONBOARDED_DATE = "onboarded_date"


class ProjectSortOrderEnum(StrEnum):
    """Valid sort_order values for projects endpoint."""

    ASC = "asc"
    DESC = "desc"


class ProjectActionEnum(StrEnum):
    """Valid action values for the project action endpoint."""

    MARK_NOT_APPLICABLE = "mark_not_applicable"
    MARK_COMPLETE = "mark_complete"


class ProjectActionRequest(BaseModel):
    """Combined request body for POST /projects/action.

    Handles both mark_complete and mark_not_applicable in a single request.

    - For mark_complete   : only project_id, project_name, action are required.
    - For mark_not_applicable : project_id, project_name, action, reason_category,
                                comments are required; evidence_url is optional.
    """

    model_config = ConfigDict(strict=False)

    project_id: str
    """UUID of the project."""

    project_name: str
    """Name of the project."""

    action: str
    """Action to perform: mark_complete or mark_not_applicable."""

    reason_category: str | None = None
    """Reason category — required when action is mark_not_applicable."""

    comments: str | None = None
    """Detailed comments — required when action is mark_not_applicable."""

    evidence_url: str | None = None
    """Pre-uploaded S3 URL of evidence file (optional, mark_not_applicable only)."""

    @model_validator(mode="after")
    def validate_not_applicable_fields(self) -> "ProjectActionRequest":
        """Enforce required fields when action is mark_not_applicable."""
        if self.action == ProjectActionEnum.MARK_NOT_APPLICABLE:
            if not self.reason_category or not self.reason_category.strip():
                raise ValueError("reason_category is required for mark_not_applicable action")
            if not self.comments or not self.comments.strip():
                raise ValueError("comments is required for mark_not_applicable action")
        return self


class ProjectsQueryParams(BaseModel):
    """Validated query parameters for the GET /projects endpoint."""

    model_config = ConfigDict(strict=False)

    period: str | None = None
    """Time period filter."""

    search: str | None = None
    """Free text search on project name."""

    status: str | None = None
    """Comma-separated status IDs."""

    client: str | None = None
    """Comma-separated client IDs."""

    specialization: str | None = None
    """Comma-separated specialization IDs."""

    offset: int = 0
    """Number of items to skip for pagination."""

    limit: int = 10
    """Number of items per page."""

    sort_by: str | None = None
    """Field to sort by: project, onboarded_date."""

    sort_order: str | None = None
    """Sort direction: asc, desc."""
