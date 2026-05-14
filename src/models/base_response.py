"""Standardized API response envelope model."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class BaseResponse(BaseModel):
    """Standard envelope for all API responses.

    All endpoints return this structure regardless of success or failure.
    """

    model_config = ConfigDict(strict=False)

    status_code: int
    """HTTP status code matching the response status."""

    status: Literal["success", "failed", "error"]
    """Response category: success for 2xx, failed for 4xx, error for 5xx."""

    message: str = Field(max_length=256)
    """Human-readable message describing the result."""

    data: Any
    """Payload object for success responses, empty array for errors."""
