"""Request DTOs for the Overview endpoint query parameters."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class PeriodEnum(StrEnum):
    """Valid period filter values (case-sensitive).

    Maps to day counts via PERIOD_DAYS_MAP in settings.
    """

    LAST_WEEK = "last_week"
    LAST_MONTH = "last_month"
    LAST_3_MONTHS = "last_3_months"


class OverviewQueryParams(BaseModel):
    """Validated query parameters for the overview endpoint."""

    model_config = ConfigDict(strict=False)

    period: str | None = None
    """Period filter (last_week, last_month, last_3_months). Defaults to last_week."""

    specialization: str | None = None
    """Comma-separated specialization UUIDs to filter by."""
