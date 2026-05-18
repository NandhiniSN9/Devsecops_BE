"""Response DTOs for the Settings endpoint."""

import uuid

from pydantic import BaseModel, ConfigDict


class EmailRecipientResponse(BaseModel):
    """Single email recipient in the settings response."""

    model_config = ConfigDict(strict=False)

    email_recipient_id: uuid.UUID
    """Unique identifier for the recipient record."""

    alert_recipient: str
    """Email address of the recipient."""


class SettingsDataResponse(BaseModel):
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

    email_recipients: list[EmailRecipientResponse] = []
    """List of active email recipients for this specialization."""
