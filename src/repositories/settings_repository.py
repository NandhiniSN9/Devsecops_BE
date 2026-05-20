"""Repository for settings data access operations.

Provides CRUD operations for settings and email recipient management.
"""

import asyncio
import traceback
import uuid
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from src.repositories.schema.email_recipient import EmailRecipient
from src.repositories.schema.setting import Setting
from src.repositories.schema.specialization import Specialization
from src.utils.logger import logger


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
        try:
            stmt = select(Specialization).where(
                Specialization.specialization_id == specialization_id,
                Specialization.is_active == 1,
            )
            result = await self._session.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as db_exc:
            logger.error("Database error in get_specialization", error=str(db_exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(db_exc),
                error_function="get_specialization",
                error_file="src/repositories/settings_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise
        except Exception as exc:
            logger.error("Unexpected error in get_specialization", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="get_specialization",
                error_file="src/repositories/settings_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def get_settings_by_specialization(self, specialization_id: uuid.UUID) -> Setting | None:
        """Get the active settings record for a specialization.

        Args:
            specialization_id: UUID of the specialization.

        Returns:
            Setting record or None if not found.
        """
        try:
            stmt = select(Setting).where(
                Setting.specialization_id == specialization_id,
                Setting.is_active == 1,
            )
            result = await self._session.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as db_exc:
            logger.error("Database error in get_settings_by_specialization", error=str(db_exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(db_exc),
                error_function="get_settings_by_specialization",
                error_file="src/repositories/settings_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise
        except Exception as exc:
            logger.error("Unexpected error in get_settings_by_specialization", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="get_settings_by_specialization",
                error_file="src/repositories/settings_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def get_email_recipients(self, specialization_id: uuid.UUID) -> list[EmailRecipient]:
        """Get all active email recipients for a specialization.

        Args:
            specialization_id: UUID of the specialization.

        Returns:
            List of active EmailRecipient records.
        """
        try:
            stmt = select(EmailRecipient).where(
                EmailRecipient.specialization_id == specialization_id,
                EmailRecipient.is_active == 1,
            )
            result = await self._session.execute(stmt)
            return list(result.scalars().all())
        except SQLAlchemyError as db_exc:
            logger.error("Database error in get_email_recipients", error=str(db_exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(db_exc),
                error_function="get_email_recipients",
                error_file="src/repositories/settings_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise
        except Exception as exc:
            logger.error("Unexpected error in get_email_recipients", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="get_email_recipients",
                error_file="src/repositories/settings_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

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
        try:
            for field_name, value in fields.items():
                setattr(setting, field_name, value)
            setting.modified_at = datetime.utcnow()
            setting.modified_by = modified_by
            await self._session.flush()
            return setting
        except SQLAlchemyError as db_exc:
            logger.error("Database error in update_setting_fields", error=str(db_exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(db_exc),
                error_function="update_setting_fields",
                error_file="src/repositories/settings_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise
        except Exception as exc:
            logger.error("Unexpected error in update_setting_fields", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="update_setting_fields",
                error_file="src/repositories/settings_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

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
        try:
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
        except SQLAlchemyError as db_exc:
            logger.error("Database error in add_email_recipient", error=str(db_exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(db_exc),
                error_function="add_email_recipient",
                error_file="src/repositories/settings_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise
        except Exception as exc:
            logger.error("Unexpected error in add_email_recipient", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="add_email_recipient",
                error_file="src/repositories/settings_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def get_recipient_by_id(self, email_recipient_id: uuid.UUID) -> EmailRecipient | None:
        """Get an active email recipient by ID.

        Args:
            email_recipient_id: UUID of the recipient record.

        Returns:
            EmailRecipient record or None if not found/inactive.
        """
        try:
            stmt = select(EmailRecipient).where(
                EmailRecipient.email_recipient_id == email_recipient_id,
                EmailRecipient.is_active == 1,
            )
            result = await self._session.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as db_exc:
            logger.error("Database error in get_recipient_by_id", error=str(db_exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(db_exc),
                error_function="get_recipient_by_id",
                error_file="src/repositories/settings_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise
        except Exception as exc:
            logger.error("Unexpected error in get_recipient_by_id", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="get_recipient_by_id",
                error_file="src/repositories/settings_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def check_duplicate_recipient(
        self, specialization_id: uuid.UUID, alert_recipient: str
    ) -> EmailRecipient | None:
        """Find an email recipient by specialization and email, regardless of is_active.

        Args:
            specialization_id: UUID of the specialization.
            alert_recipient: Email address to check.

        Returns:
            EmailRecipient record or None if not found.
        """
        try:
            stmt = select(EmailRecipient).where(
                EmailRecipient.specialization_id == specialization_id,
                EmailRecipient.alert_recipient == alert_recipient,
            )
            result = await self._session.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as db_exc:
            logger.error("Database error in check_duplicate_recipient", error=str(db_exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(db_exc),
                error_function="check_duplicate_recipient",
                error_file="src/repositories/settings_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise
        except Exception as exc:
            logger.error("Unexpected error in check_duplicate_recipient", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="check_duplicate_recipient",
                error_file="src/repositories/settings_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def reactivate_recipient(
        self, recipient: EmailRecipient, modified_by: str
    ) -> None:
        """Reactivate a soft-deleted email recipient by setting is_active = 1.

        Args:
            recipient: The EmailRecipient ORM instance to reactivate.
            modified_by: Identifier of who made the change.
        """
        try:
            recipient.is_active = 1
            recipient.modified_at = datetime.utcnow()
            recipient.modified_by = modified_by
            await self._session.flush()
        except SQLAlchemyError as db_exc:
            logger.error("Database error in reactivate_recipient", error=str(db_exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(db_exc),
                error_function="reactivate_recipient",
                error_file="src/repositories/settings_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise
        except Exception as exc:
            logger.error("Unexpected error in reactivate_recipient", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="reactivate_recipient",
                error_file="src/repositories/settings_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def soft_delete_recipient(
        self, recipient: EmailRecipient, modified_by: str
    ) -> None:
        """Soft-delete an email recipient by setting is_active = 0.

        Args:
            recipient: The EmailRecipient ORM instance to deactivate.
            modified_by: Identifier of who made the change.
        """
        try:
            recipient.is_active = 0
            recipient.modified_at = datetime.utcnow()
            recipient.modified_by = modified_by
            await self._session.flush()
        except SQLAlchemyError as db_exc:
            logger.error("Database error in soft_delete_recipient", error=str(db_exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(db_exc),
                error_function="soft_delete_recipient",
                error_file="src/repositories/settings_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise
        except Exception as exc:
            logger.error("Unexpected error in soft_delete_recipient", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="soft_delete_recipient",
                error_file="src/repositories/settings_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise
