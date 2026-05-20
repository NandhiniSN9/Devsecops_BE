"""Request DTOs for the Projects endpoint query parameters and action body."""

from enum import StrEnum
from pydantic import BaseModel, ConfigDict


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
