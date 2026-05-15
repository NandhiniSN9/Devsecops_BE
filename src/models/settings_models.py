"""Pydantic models for the Settings endpoint request/response payloads."""

import uuid
from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ScheduleEnum(str, Enum):
    """Accepted schedule values for email_digest and at_risk_alert."""

    DAILY = "daily"
    WEEKLY = "weekly"
    BI_WEEKLY = "bi-weekly"
    MONTHLY = "monthly"
    NOT_REQUIRED = "not_required"


class EmailRecipientResponse(BaseModel):
    """Single email recipient in the settings response."""

    model_config = ConfigDict(strict=False)

    email_recipient_id: uuid.UUID
    """Unique identifier for the recipient record."""

    alert_recipient: str
    """Email address of the recipient."""


class SettingsData(BaseModel):
    """Full settings response payload for a specialization."""

    model_config = ConfigDict(strict=False)

    setting_id: uuid.UUID
    """Unique identifier for the settings record."""

    specialization_id: uuid.UUID
    """UUID of the specialization."""

    specialization_name: str
    """Display name of the specialization."""

    at_risk_threshold: int
    """Days since onboarding without repo before project is at-risk."""

    email_digest: str | None = None
    """Email digest schedule value (daily/weekly/bi-weekly/monthly/not_required)."""

    at_risk_alert: str | None = None
    """At-risk alert schedule value (daily/weekly/bi-weekly/monthly/not_required)."""

    last_synced: str | None = None
    """Timestamp of the last sync operation in ISO format."""

    email_recipients: list[EmailRecipientResponse] = []
    """List of active email recipients for this specialization."""


class EmailRecipientAction(BaseModel):
    """Single add/remove action for email recipient management."""

    model_config = ConfigDict(strict=False)

    action: Literal["add", "remove"]
    """Action type: 'add' to create a new recipient, 'remove' to soft-delete."""

    alert_recipient: EmailStr | None = None
    """Email address to add (required when action is 'add')."""

    email_recipient_id: uuid.UUID | None = None
    """UUID of the recipient to remove (required when action is 'remove')."""


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
