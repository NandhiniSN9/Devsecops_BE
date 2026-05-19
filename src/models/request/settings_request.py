"""Request DTOs for the Settings endpoints."""

import uuid
from typing import Literal
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class EmailRecipientAction(BaseModel):
    """Single add/remove action for email recipient management."""

    model_config = ConfigDict(strict=False)

    action: Literal["add", "remove"]
    """Action type: 'add' to create a new recipient, 'remove' to soft-delete."""

    alert_recipient: list[EmailStr] | None = None
    """List of email addresses to add (required when action is 'add')."""

    email_recipient_id: list[uuid.UUID] | None = None
    """List of UUIDs of the recipients to remove (required when action is 'remove')."""


class SettingsUpdateRequest(BaseModel):
    """Request body for PUT /api/v1/settings/manage."""

    model_config = ConfigDict(strict=False)

    specialization_id: uuid.UUID
    """Required. UUID of the specialization to update settings for."""

    at_risk_threshold: int | None = Field(default=None, ge=1)
    """Optional. Days threshold, minimum 1."""

    email_digest: str | None = None
    """Optional. Schedule value (daily/weekly/bi-weekly/monthly/not_required)."""

    at_risk_alert: str | None = None
    """Optional. Schedule value (daily/weekly/bi-weekly/monthly/not_required)."""

    email_recipients: list[EmailRecipientAction] | None = None
    """Optional. List of add/remove actions for email recipients."""
