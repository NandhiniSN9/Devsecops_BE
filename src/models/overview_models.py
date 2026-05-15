"""Pydantic models for the Overview endpoint response payload."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class KpiTile(BaseModel):
    """Single KPI metric card with count, trend direction, and change value."""

    model_config = ConfigDict(strict=False)

    count: int = Field(ge=0)
    """Current metric value (non-negative)."""

    trend: Literal["increase", "decrease", "flat"] | None
    """Direction indicator: increase, decrease, flat, or null when no data exists."""

    change: int = Field(ge=0)
    """Absolute change value from the prior period."""


class OverviewMetrics(BaseModel):
    """All six KPI tiles for the overview dashboard."""

    model_config = ConfigDict(strict=False)

    total_projects: KpiTile
    completed: KpiTile
    active: KpiTile
    inactive: KpiTile
    at_risk: KpiTile
    not_applicable: KpiTile


class StatusBreakdownItem(BaseModel):
    """Individual status entry in the distribution breakdown."""

    model_config = ConfigDict(strict=False)

    status: str
    """Status name from the statuses table."""

    count: int = Field(ge=0)
    """Number of projects with this status."""

    percentage: float = Field(ge=0.0, le=100.0)
    """Percentage of total projects, rounded to one decimal place."""


class StatusDistribution(BaseModel):
    """Project status breakdown with total count and per-status details."""

    model_config = ConfigDict(strict=False)

    total: int = Field(ge=0)
    """Sum of all status counts in the breakdown."""

    breakdown: list[StatusBreakdownItem]
    """Per-status details sorted alphabetically by status name."""


class AttentionBanner(BaseModel):
    """Risk notification banner with severity level."""

    model_config = ConfigDict(strict=False)

    message: str = Field(max_length=200)
    """Alert text including the at-risk count when applicable."""

    at_risk_count: int = Field(ge=0)
    """Number of at-risk projects."""

    severity: Literal["critical", "warning", "info"]
    """Severity level based on at_risk_count thresholds."""


class OverviewData(BaseModel):
    """Combined overview response payload."""

    model_config = ConfigDict(strict=False)

    metrics: OverviewMetrics
    status_distribution: StatusDistribution
