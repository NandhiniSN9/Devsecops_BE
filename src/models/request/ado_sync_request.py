"""Request DTOs for the ADO Sync endpoint."""

from pydantic import BaseModel, ConfigDict


class AdoSyncRequest(BaseModel):
    """Request body for POST /api/v1/sync/ado."""

    model_config = ConfigDict(strict=False)
