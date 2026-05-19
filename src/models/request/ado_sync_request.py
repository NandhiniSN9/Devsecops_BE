"""Request DTOs for the ADO Sync endpoint."""

import uuid

from pydantic import BaseModel, ConfigDict


class AdoSyncRequest(BaseModel):
    """Request body for POST /api/v1/sync/ado."""

    model_config = ConfigDict(strict=False)

    specialization_id: uuid.UUID | None = None
    """Optional UUID of the specialization to sync. Null syncs all."""
