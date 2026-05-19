"""Repository for settings data access operations.

Provides CRUD operations for settings and email recipient management.
"""

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.schema.email_recipient import EmailRecipient
from src.repositories.schema.setting import Setting
from src.repositories.schema.specialization import Specialization


class SettingsRepository:
    """Data access layer for settings queries."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_specialization(self, specialization_id: uuid.UUID) -> Specialization | None:
        """Get an active specialization by ID.

        Args:
            specialization_id: UUID of the specialization.

        Returns:
            Specialization record or None if not found/inactive.
        """
        stmt = select(Specialization).where(
            Specialization.specialization_id == specialization_id,
            Specialization.is_active == 1,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_settings_with_recipients(
        self, specialization_id: uuid.UUID
    ) -> tuple[Setting | None, list[EmailRecipient]]:
        """Get settings and email recipients for a specialization using a single joined query.

        Args:
            specialization_id: UUID of the specialization.

        Returns:
            Tuple of (Setting or None, list of EmailRecipient).
            If no recipients exist, returns an empty list.
        """
        stmt = (
            select(Setting, EmailRecipient)
            .outerjoin(
                EmailRecipient,
                (EmailRecipient.setting_id == Setting.setting_id)
                & (EmailRecipient.is_active == 1),
            )
            .where(
                Setting.specialization_id == specialization_id,
                Setting.is_active == 1,
            )
        )
        result = await self._session.execute(stmt)
        rows = result.all()

        if not rows:
            return None, []

        setting = rows[0][0]
        recipients = [row[1] for row in rows if row[1] is not None]

        return setting, recipients


    async def update_setting_fields(
        self,
        setting: Setting,
        fields: dict,
        modified_by: str,
    ) -> Setting:
        """Update specific fields on a settings record.

        Args:
            setting: The Setting ORM instance to update.
            fields: Dictionary of field names to new values.
            modified_by: Identifier of who made the change.

        Returns:
            The updated Setting instance.
        """
        for field_name, value in fields.items():
            setattr(setting, field_name, value)
        setting.modified_at = datetime.utcnow()
        setting.modified_by = modified_by
        await self._session.flush()
        return setting

    async def add_email_recipient(
        self,
        setting_id: uuid.UUID,
        specialization_id: uuid.UUID,
        alert_recipient: str,
        created_by: str,
    ) -> EmailRecipient:
        """Add a new email recipient record.

        Args:
            setting_id: FK to the settings record.
            specialization_id: FK to the specialization.
            alert_recipient: Email address of the recipient.
            created_by: Identifier of who created the record.

        Returns:
            The newly created EmailRecipient instance.
        """
        recipient = EmailRecipient(
            email_recipient_id=uuid.uuid4(),
            setting_id=setting_id,
            specialization_id=specialization_id,
            alert_recipient=alert_recipient,
            created_by=created_by,
            is_active=1,
        )
        self._session.add(recipient)
        await self._session.flush()
        return recipient

    async def get_recipient_by_id(self, email_recipient_id: uuid.UUID) -> EmailRecipient | None:
        """Get an active email recipient by ID.

        Args:
            email_recipient_id: UUID of the recipient record.

        Returns:
            EmailRecipient record or None if not found/inactive.
        """
        stmt = select(EmailRecipient).where(
            EmailRecipient.email_recipient_id == email_recipient_id,
            EmailRecipient.is_active == 1,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def check_duplicate_recipient(
        self, specialization_id: uuid.UUID, alert_recipient: str
    ) -> bool:
        """Check if an email recipient already exists for a specialization.

        Args:
            specialization_id: UUID of the specialization.
            alert_recipient: Email address to check.

        Returns:
            True if a duplicate active recipient exists.
        """
        stmt = select(EmailRecipient).where(
            EmailRecipient.specialization_id == specialization_id,
            EmailRecipient.alert_recipient == alert_recipient,
            EmailRecipient.is_active == 1,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def soft_delete_recipient(
        self, recipient: EmailRecipient, modified_by: str
    ) -> None:
        """Soft-delete an email recipient by setting is_active = 0.

        Args:
            recipient: The EmailRecipient ORM instance to deactivate.
            modified_by: Identifier of who made the change.
        """
        recipient.is_active = 0
        recipient.modified_at = datetime.utcnow()
        recipient.modified_by = modified_by
        await self._session.flush()

    async def commit(self) -> None:
        """Commit the current transaction."""
        await self._session.commit()
