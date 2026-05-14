"""Pydantic models for the Filters endpoint response payload."""

from pydantic import BaseModel, ConfigDict


class FilterItem(BaseModel):
    """Generic id/name pair for filter dropdown options."""

    model_config = ConfigDict(strict=False)

    id: str
    """UUID string identifier."""

    name: str
    """Display name for the filter option."""


class FiltersData(BaseModel):
    """Filter dropdown options for specializations, clients, and statuses."""

    model_config = ConfigDict(strict=False)

    specializations: list[FilterItem]
    """Active specializations sorted alphabetically by name."""

    clients: list[FilterItem]
    """Distinct active clients sorted alphabetically by name."""

    statuses: list[FilterItem]
    """Active statuses sorted alphabetically by name."""
