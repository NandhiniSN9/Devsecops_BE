"""Response DTOs for the Filters endpoint."""

from pydantic import BaseModel, ConfigDict


class FilterItemResponse(BaseModel):
    """Generic id/name pair for filter dropdown options."""

    model_config = ConfigDict(strict=False)

    id: str
    """UUID string identifier."""

    name: str
    """Display name for the filter option."""


class FiltersDataResponse(BaseModel):
    """Filter dropdown options for specializations, clients, and statuses."""

    model_config = ConfigDict(strict=False)

    specializations: list[FilterItemResponse]
    """Active specializations sorted alphabetically by name."""

    clients: list[FilterItemResponse]
    """Distinct active clients sorted alphabetically by name."""

    statuses: list[FilterItemResponse]
    """Active statuses sorted alphabetically by name."""
