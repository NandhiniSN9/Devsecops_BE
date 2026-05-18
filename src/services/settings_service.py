"""Settings service for managing specialization configuration and email recipients."""

import uuid

from src.dtos.request.settings_request import EmailRecipientAction, SettingsUpdateRequest
from src.dtos.response.settings_response import EmailRecipientResponse, SettingsDataResponse
from src.repositories.settings_repository import SettingsRepository
from src.utils.exceptions import InvalidParameterError, NotFoundError

# Valid schedule values for email_digest and at_risk_alert
VALID_SCHEDULE_VALUES = ["daily", "weekly", "bi-weekly", "monthly", "not_required"]

# Service identifier for modified_by field
SETTINGS_SERVICE_IDENTIFIER = "settings_service"


class SettingsService:
    """Service for settings retrieval and update operations."""

    def __init__(self, settings_repo: SettingsRepository) -> None:
        """Initialize with repository dependency."""
        self._settings_repo = settings_repo

    async def get_settings(self, specialization_id_str: str) -> SettingsDataResponse:
        """Retrieve settings for a specialization.

        Args:
            specialization_id_str: UUID string from path parameter.

        Returns:
            SettingsDataResponse with full settings and email recipients.

        Raises:
            InvalidParameterError: If UUID format is invalid.
            NotFoundError: If specialization or settings not found.
        """
        specialization_id = self._validate_uuid(specialization_id_str, "specializationId")

        specialization = await self._settings_repo.get_specialization(specialization_id)
        if not specialization:
            raise NotFoundError("Specialization not found")

        setting = await self._settings_repo.get_settings_by_specialization(specialization_id)
        if not setting:
            raise NotFoundError("Settings not found for this specialization")

        recipients = await self._settings_repo.get_email_recipients(specialization_id)

        return SettingsDataResponse(
            setting_id=setting.setting_id,
            specialization_id=specialization.specialization_id,
            specialization_name=specialization.specialization_name,
            at_risk_threshold=setting.at_risk_threshold,
            email_digest=setting.email_digest,
            at_risk_alert=setting.at_risk_alert,
            last_synced=setting.last_synced.isoformat() if setting.last_synced else None,
            email_recipients=[
                EmailRecipientResponse(
                    email_recipient_id=r.email_recipient_id,
                    alert_recipient=r.alert_recipient,
                )
                for r in recipients
            ],
        )

    async def update_settings(self, request: SettingsUpdateRequest) -> SettingsDataResponse:
        """Update settings for a specialization (partial update).

        Args:
            request: Validated update request with fields to change.

        Returns:
            SettingsData with the updated settings.

        Raises:
            InvalidParameterError: If field values are invalid.
            NotFoundError: If specialization or settings not found.
        """
        specialization = await self._settings_repo.get_specialization(request.specialization_id)
        if not specialization:
            raise NotFoundError("Specialization not found")

        setting = await self._settings_repo.get_settings_by_specialization(request.specialization_id)
        if not setting:
            raise NotFoundError("Settings not found for this specialization")

        # Build update fields dict (only provided fields)
        update_fields: dict = {}

        if request.at_risk_threshold is not None:
            update_fields["at_risk_threshold"] = request.at_risk_threshold

        if request.email_digest is not None:
            self._validate_schedule_value(request.email_digest, "email_digest")
            update_fields["email_digest"] = request.email_digest

        if request.at_risk_alert is not None:
            self._validate_schedule_value(request.at_risk_alert, "at_risk_alert")
            update_fields["at_risk_alert"] = request.at_risk_alert

        # Apply settings field updates
        if update_fields:
            await self._settings_repo.update_setting_fields(
                setting, update_fields, SETTINGS_SERVICE_IDENTIFIER
            )

        # Process email recipient actions
        if request.email_recipients:
            await self._process_recipient_actions(
                request.email_recipients,
                setting.setting_id,
                request.specialization_id,
            )

        # Commit all changes in one transaction
        await self._settings_repo.commit()

        # Return updated settings
        return await self.get_settings(str(request.specialization_id))

    async def _process_recipient_actions(
        self,
        actions: list[EmailRecipientAction],
        setting_id: uuid.UUID,
        specialization_id: uuid.UUID,
    ) -> None:
        """Process add/remove actions for email recipients.

        Args:
            actions: List of recipient actions to process.
            setting_id: FK to the settings record.
            specialization_id: FK to the specialization.

        Raises:
            InvalidParameterError: If action validation fails.
        """
        for action_item in actions:
            if action_item.action == "add":
                if not action_item.alert_recipient:
                    raise InvalidParameterError(
                        "alert_recipient is required when action is 'add'"
                    )

                # Check for duplicate
                is_duplicate = await self._settings_repo.check_duplicate_recipient(
                    specialization_id, action_item.alert_recipient
                )
                if is_duplicate:
                    raise InvalidParameterError("Recipient already exists")

                await self._settings_repo.add_email_recipient(
                    setting_id=setting_id,
                    specialization_id=specialization_id,
                    alert_recipient=action_item.alert_recipient,
                    created_by=SETTINGS_SERVICE_IDENTIFIER,
                )

            elif action_item.action == "remove":
                if not action_item.email_recipient_id:
                    raise InvalidParameterError(
                        "email_recipient_id is required when action is 'remove'"
                    )

                recipient = await self._settings_repo.get_recipient_by_id(
                    action_item.email_recipient_id
                )
                if not recipient:
                    raise InvalidParameterError("Recipient not found or already removed")

                await self._settings_repo.soft_delete_recipient(
                    recipient, SETTINGS_SERVICE_IDENTIFIER
                )

    @staticmethod
    def _validate_uuid(value: str, field_name: str) -> uuid.UUID:
        """Validate and parse a UUID string.

        Args:
            value: String to parse as UUID.
            field_name: Name of the field for error messages.

        Returns:
            Parsed UUID.

        Raises:
            InvalidParameterError: If format is invalid.
        """
        try:
            return uuid.UUID(value)
        except (ValueError, AttributeError):
            raise InvalidParameterError(f"Invalid {field_name} format")

    @staticmethod
    def _validate_schedule_value(value: str, field_name: str) -> None:
        """Validate a schedule field value.

        Args:
            value: The schedule value to validate.
            field_name: Name of the field for error messages.

        Raises:
            InvalidParameterError: If value is not in accepted list.
        """
        if value not in VALID_SCHEDULE_VALUES:
            raise InvalidParameterError(
                f"{field_name} must be one of {VALID_SCHEDULE_VALUES}"
            )
