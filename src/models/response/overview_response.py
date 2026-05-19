"""Response DTOs for the Overview endpoint."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class KpiTileResponse(BaseModel):
    """Single KPI metric card with count, trend direction, and change value."""

    model_config = ConfigDict(strict=False)

    count: int = Field(ge=0)
    """Current metric value (non-negative)."""

    trend: Literal["increase", "decrease", "flat"] | None
    """Direction indicator: increase, decrease, flat, or null when no data exists."""

    change: int = Field(ge=0)
    """Absolute change value from the prior period."""


class OverviewMetricsResponse(BaseModel):
    """All seven KPI tiles for the overview dashboard."""

    model_config = ConfigDict(strict=False)

    total_projects: KpiTileResponse
    adopted: KpiTileResponse
    completed: KpiTileResponse
    active: KpiTileResponse
    inactive: KpiTileResponse
    at_risk: KpiTileResponse
    not_applicable: KpiTileResponse


class StatusBreakdownItemResponse(BaseModel):
    """Individual status entry in the distribution breakdown."""

    model_config = ConfigDict(strict=False)

    status: str
    """Status name from the statuses table."""

    count: int = Field(ge=0)
    """Number of projects with this status."""

    percentage: float = Field(ge=0.0, le=100.0)
    """Percentage of total projects, rounded to one decimal place."""


class StatusDistributionResponse(BaseModel):
    """Project status breakdown with total count and per-status details."""

    model_config = ConfigDict(strict=False)

    total: int = Field(ge=0)
    """Sum of all status counts in the breakdown."""

    breakdown: list[StatusBreakdownItemResponse]
    """Per-status details sorted alphabetically by status name."""


class SyncDetailResponse(BaseModel):
    """Sync status detail containing last sync time and in-progress indicator."""

    model_config = ConfigDict(strict=False)

    last_sync_datetime: str | None
    """Most recent sync timestamp in 'DD Mon YYYY, HH:MM' format, or null if never synced."""

    is_sync_in_progress: bool
    """Whether an ADO sync operation is currently in progress."""


class OverviewDataResponse(BaseModel):
    """Combined overview response payload."""

    model_config = ConfigDict(strict=False)

    sync_detail: SyncDetailResponse
    """Sync status information including last sync time and in-progress state."""

    metrics: OverviewMetricsResponse
    status_distribution: StatusDistributionResponse
