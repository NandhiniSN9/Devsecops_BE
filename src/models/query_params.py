"""Query parameter validation models for the Overview Dashboard API."""

from enum import StrEnum


class PeriodEnum(StrEnum):
    """Valid period filter values (case-sensitive).

    Maps to day counts via PERIOD_DAYS_MAP in settings.
    """

    LAST_WEEK = "last_week"
    LAST_MONTH = "last_month"
    LAST_3_MONTHS = "last_3_months"
