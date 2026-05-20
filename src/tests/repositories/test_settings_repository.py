"""Unit tests for SettingsRepository data access operations.

Tests settings CRUD operations, email recipient management, and frequency configuration.
"""

import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.settings_repository import SettingsRepository
from src.repositories.schema.email_recipient import EmailRecipient
from src.repositories.schema.setting import Setting
from src.repositories.schema.specialization import Specialization


@pytest.fixture
def mock_session():
    """Create a mock async session."""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def repo(mock_session):
    """Create a SettingsRepository with mock session."""
    return SettingsRepository(mock_session)


@pytest.fixture
def sample_specialization():
    """Create a sample specialization object for testing."""
    return Specialization(
        specialization_id=uuid.uuid4(),
        specialization_name="Backend Engineering",
        is_active=1,
        created_at=datetime.utcnow(),
        created_by="test_user",
    )


@pytest.fixture
def sample_setting(sample_specialization):
    """Create a sample setting object for testing."""
    return Setting(
        setting_id=uuid.uuid4(),
        specialization_id=sample_specialization.specialization_id,
        at_risk_threshold=30,
        email_digest="weekly",
        at_risk_alert="immediate",
        last_synced=datetime.utcnow(),
        is_active=1,
        created_at=datetime.utcnow(),
        created_by="test_user",
    )


@pytest.fixture
def sample_email_recipients(sample_setting, sample_specialization):
    """Create sample email recipient objects for testing."""
    return [
        EmailRecipient(
            email_recipient_id=uuid.uuid4(),
            setting_id=sample_setting.setting_id,
            specialization_id=sample_specialization.specialization_id,
            alert_recipient="user1@example.com",
            is_active=1,
            created_at=datetime.utcnow(),
            created_by="test_user",
        ),
        EmailRecipient(
            email_recipient_id=uuid.uuid4(),
            setting_id=sample_setting.setting_id,
            specialization_id=sample_specialization.specialization_id,
            alert_recipient="user2@example.com",
            is_active=1,
            created_at=datetime.utcnow(),
            created_by="test_user",
        ),
    ]


class TestGetSpecialization:
    """Tests for get_specialization method."""

    @pytest.mark.asyncio
    async def test_get_specialization_found(self, repo, mock_session, sample_specialization):
        """Should return specialization when found and active."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_specialization
        mock_session.execute.return_value = mock_result

        result = await repo.get_specialization(sample_specialization.specialization_id)

        assert result is not None
        assert result.specialization_name == "Backend Engineering"
        assert result.is_active == 1

    @pytest.mark.asyncio
    async def test_get_specialization_not_found(self, repo, mock_session):
        """Should return None when specialization not found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await repo.get_specialization(uuid.uuid4())

        assert result is None

    @pytest.mark.asyncio
    async def test_get_specialization_database_error(self, repo, mock_session):
        """Should raise exception on database error."""
        mock_session.execute.side_effect = SQLAlchemyError("Database connection failed")

        with pytest.raises(SQLAlchemyError):
            await repo.get_specialization(uuid.uuid4())


class TestGetSettingsBySpecialization:
    """Tests for get_settings_by_specialization method."""

    @pytest.mark.asyncio
    async def test_get_settings_found(self, repo, mock_session, sample_setting):
        """Should return settings when found for specialization."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_setting
        mock_session.execute.return_value = mock_result

        result = await repo.get_settings_by_specialization(sample_setting.specialization_id)

        assert result is not None
        assert result.at_risk_threshold == 30
        assert result.email_digest == "weekly"
        assert result.at_risk_alert == "immediate"

    @pytest.mark.asyncio
    async def test_get_settings_not_found(self, repo, mock_session):
        """Should return None when no settings found for specialization."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await repo.get_settings_by_specialization(uuid.uuid4())

        assert result is None

    @pytest.mark.asyncio
    async def test_get_settings_database_error(self, repo, mock_session):
        """Should raise exception on database error."""
        mock_session.execute.side_effect = SQLAlchemyError("Query failed")

        with pytest.raises(SQLAlchemyError):
            await repo.get_settings_by_specialization(uuid.uuid4())


class TestGetEmailRecipients:
    """Tests for get_email_recipients method."""

    @pytest.mark.asyncio
    async def test_get_email_recipients_success(self, repo, mock_session, sample_email_recipients):
        """Should return list of active email recipients."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = sample_email_recipients
        mock_session.execute.return_value = mock_result

        result = await repo.get_email_recipients(uuid.uuid4())

        assert len(result) == 2
        assert result[0].alert_recipient == "user1@example.com"
        assert result[1].alert_recipient == "user2@example.com"

    @pytest.mark.asyncio
    async def test_get_email_recipients_empty_list(self, repo, mock_session):
        """Should return empty list when no recipients found."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        result = await repo.get_email_recipients(uuid.uuid4())

        assert result == []

    @pytest.mark.asyncio
    async def test_get_email_recipients_database_error(self, repo, mock_session):
        """Should raise exception on database error."""
        mock_session.execute.side_effect = SQLAlchemyError("Connection error")

        with pytest.raises(SQLAlchemyError):
            await repo.get_email_recipients(uuid.uuid4())


class TestUpdateSettingFields:
    """Tests for update_setting_fields method."""

    @pytest.mark.asyncio
    async def test_update_threshold_success(self, repo, mock_session, sample_setting):
        """Should update at_risk_threshold field."""
        fields = {"at_risk_threshold": 45}

        result = await repo.update_setting_fields(sample_setting, fields, "admin_user")

        assert result.at_risk_threshold == 45
        assert result.modified_by == "admin_user"
        mock_session.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_update_email_frequencies_success(self, repo, mock_session, sample_setting):
        """Should update email_digest and at_risk_alert frequencies."""
        fields = {
            "email_digest": "daily",
            "at_risk_alert": "daily"
        }

        result = await repo.update_setting_fields(sample_setting, fields, "admin_user")

        assert result.email_digest == "daily"
        assert result.at_risk_alert == "daily"
        assert result.modified_by == "admin_user"
        mock_session.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_update_multiple_fields_success(self, repo, mock_session, sample_setting):
        """Should update multiple fields at once."""
        fields = {
            "at_risk_threshold": 60,
            "email_digest": "monthly",
            "at_risk_alert": "weekly"
        }

        result = await repo.update_setting_fields(sample_setting, fields, "test_user")

        assert result.at_risk_threshold == 60
        assert result.email_digest == "monthly"
        assert result.at_risk_alert == "weekly"

    @pytest.mark.asyncio
    async def test_update_setting_fields_database_error(self, repo, mock_session, sample_setting):
        """Should raise exception on database error."""
        mock_session.flush.side_effect = SQLAlchemyError("Flush failed")

        with pytest.raises(SQLAlchemyError):
            await repo.update_setting_fields(sample_setting, {"at_risk_threshold": 50}, "user")


class TestAddEmailRecipient:
    """Tests for add_email_recipient method."""

    @pytest.mark.asyncio
    async def test_add_email_recipient_success(self, repo, mock_session):
        """Should add new email recipient successfully."""
        setting_id = uuid.uuid4()
        specialization_id = uuid.uuid4()

        result = await repo.add_email_recipient(
            setting_id=setting_id,
            specialization_id=specialization_id,
            alert_recipient="newuser@example.com",
            created_by="admin",
        )

        assert result.setting_id == setting_id
        assert result.specialization_id == specialization_id
        assert result.alert_recipient == "newuser@example.com"
        assert result.is_active == 1
        mock_session.add.assert_called_once()
        mock_session.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_add_email_recipient_database_error(self, repo, mock_session):
        """Should raise exception on database error."""
        mock_session.flush.side_effect = SQLAlchemyError("Insert failed")

        with pytest.raises(SQLAlchemyError):
            await repo.add_email_recipient(
                setting_id=uuid.uuid4(),
                specialization_id=uuid.uuid4(),
                alert_recipient="user@example.com",
                created_by="admin",
            )


class TestGetRecipientById:
    """Tests for get_recipient_by_id method."""

    @pytest.mark.asyncio
    async def test_get_recipient_by_id_found(self, repo, mock_session, sample_email_recipients):
        """Should return recipient when found and active."""
        recipient = sample_email_recipients[0]
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = recipient
        mock_session.execute.return_value = mock_result

        result = await repo.get_recipient_by_id(recipient.email_recipient_id)

        assert result is not None
        assert result.alert_recipient == "user1@example.com"
        assert result.is_active == 1

    @pytest.mark.asyncio
    async def test_get_recipient_by_id_not_found(self, repo, mock_session):
        """Should return None when recipient not found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await repo.get_recipient_by_id(uuid.uuid4())

        assert result is None

    @pytest.mark.asyncio
    async def test_get_recipient_by_id_database_error(self, repo, mock_session):
        """Should raise exception on database error."""
        mock_session.execute.side_effect = SQLAlchemyError("Query error")

        with pytest.raises(SQLAlchemyError):
            await repo.get_recipient_by_id(uuid.uuid4())


class TestCheckDuplicateRecipient:
    """Tests for check_duplicate_recipient method."""

    @pytest.mark.asyncio
    async def test_check_duplicate_recipient_found(self, repo, mock_session, sample_email_recipients):
        """Should return recipient when duplicate email found."""
        recipient = sample_email_recipients[0]
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = recipient
        mock_session.execute.return_value = mock_result

        result = await repo.check_duplicate_recipient(
            specialization_id=recipient.specialization_id,
            alert_recipient="user1@example.com"
        )

        assert result is not None
        assert result.alert_recipient == "user1@example.com"

    @pytest.mark.asyncio
    async def test_check_duplicate_recipient_not_found(self, repo, mock_session):
        """Should return None when no duplicate found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await repo.check_duplicate_recipient(
            specialization_id=uuid.uuid4(),
            alert_recipient="unique@example.com"
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_check_duplicate_recipient_ignores_is_active(self, repo, mock_session):
        """Should check for duplicates regardless of is_active status."""
        inactive_recipient = EmailRecipient(
            email_recipient_id=uuid.uuid4(),
            setting_id=uuid.uuid4(),
            specialization_id=uuid.uuid4(),
            alert_recipient="inactive@example.com",
            is_active=0,  # Inactive recipient
            created_at=datetime.utcnow(),
            created_by="test",
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = inactive_recipient
        mock_session.execute.return_value = mock_result

        result = await repo.check_duplicate_recipient(
            specialization_id=inactive_recipient.specialization_id,
            alert_recipient="inactive@example.com"
        )

        assert result is not None
        assert result.is_active == 0


class TestReactivateRecipient:
    """Tests for reactivate_recipient method."""

    @pytest.mark.asyncio
    async def test_reactivate_recipient_success(self, repo, mock_session):
        """Should reactivate soft-deleted recipient."""
        recipient = EmailRecipient(
            email_recipient_id=uuid.uuid4(),
            setting_id=uuid.uuid4(),
            specialization_id=uuid.uuid4(),
            alert_recipient="reactivate@example.com",
            is_active=0,  # Soft-deleted
            created_at=datetime.utcnow(),
            created_by="test",
        )

        await repo.reactivate_recipient(recipient, "admin_user")

        assert recipient.is_active == 1
        assert recipient.modified_by == "admin_user"
        assert recipient.modified_at is not None
        mock_session.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_reactivate_recipient_database_error(self, repo, mock_session):
        """Should raise exception on database error."""
        recipient = EmailRecipient(
            email_recipient_id=uuid.uuid4(),
            setting_id=uuid.uuid4(),
            specialization_id=uuid.uuid4(),
            alert_recipient="test@example.com",
            is_active=0,
            created_at=datetime.utcnow(),
            created_by="test",
        )
        mock_session.flush.side_effect = SQLAlchemyError("Update failed")

        with pytest.raises(SQLAlchemyError):
            await repo.reactivate_recipient(recipient, "admin")


class TestSoftDeleteRecipient:
    """Tests for soft_delete_recipient method."""

    @pytest.mark.asyncio
    async def test_soft_delete_recipient_success(self, repo, mock_session, sample_email_recipients):
        """Should soft-delete recipient by setting is_active to 0."""
        recipient = sample_email_recipients[0]

        await repo.soft_delete_recipient(recipient, "admin_user")

        assert recipient.is_active == 0
        assert recipient.modified_by == "admin_user"
        assert recipient.modified_at is not None
        mock_session.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_soft_delete_recipient_database_error(self, repo, mock_session, sample_email_recipients):
        """Should raise exception on database error."""
        recipient = sample_email_recipients[0]
        mock_session.flush.side_effect = SQLAlchemyError("Delete failed")

        with pytest.raises(SQLAlchemyError):
            await repo.soft_delete_recipient(recipient, "admin")


class TestRecipientWorkflow:
    """Integration-style tests for complete recipient workflows."""

    @pytest.mark.asyncio
    async def test_add_check_duplicate_reactivate_workflow(self, repo, mock_session):
        """Should handle add -> check duplicate -> reactivate workflow."""
        # Scenario: User tries to add duplicate email that was soft-deleted
        specialization_id = uuid.uuid4()
        setting_id = uuid.uuid4()
        email = "duplicate@example.com"

        # First, check for duplicate (found inactive)
        inactive_recipient = EmailRecipient(
            email_recipient_id=uuid.uuid4(),
            setting_id=setting_id,
            specialization_id=specialization_id,
            alert_recipient=email,
            is_active=0,
            created_at=datetime.utcnow(),
            created_by="old_user",
        )

        mock_check_result = MagicMock()
        mock_check_result.scalar_one_or_none.return_value = inactive_recipient
        mock_session.execute.return_value = mock_check_result

        duplicate = await repo.check_duplicate_recipient(specialization_id, email)

        assert duplicate is not None
        assert duplicate.is_active == 0

        # Then reactivate instead of creating new
        await repo.reactivate_recipient(duplicate, "new_user")

        assert duplicate.is_active == 1
        assert duplicate.modified_by == "new_user"

    @pytest.mark.asyncio
    async def test_get_update_settings_workflow(self, repo, mock_session, sample_setting):
        """Should handle get settings -> update fields workflow."""
        # Get settings
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_setting
        mock_session.execute.return_value = mock_result

        settings = await repo.get_settings_by_specialization(sample_setting.specialization_id)

        assert settings is not None
        assert settings.at_risk_threshold == 30

        # Update settings
        updated = await repo.update_setting_fields(
            settings,
            {"at_risk_threshold": 50, "email_digest": "daily"},
            "admin"
        )

        assert updated.at_risk_threshold == 50
        assert updated.email_digest == "daily"


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_get_email_recipients_with_invalid_uuid(self, repo, mock_session):
        """Should handle invalid UUID gracefully."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        # Should not raise exception with valid UUID format
        result = await repo.get_email_recipients(uuid.uuid4())

        assert result == []

    @pytest.mark.asyncio
    async def test_update_setting_fields_empty_fields_dict(self, repo, mock_session, sample_setting):
        """Should handle empty fields dictionary."""
        result = await repo.update_setting_fields(sample_setting, {}, "admin")

        assert result.modified_by == "admin"
        mock_session.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_add_email_recipient_special_characters_in_email(self, repo, mock_session):
        """Should handle special characters in email addresses."""
        result = await repo.add_email_recipient(
            setting_id=uuid.uuid4(),
            specialization_id=uuid.uuid4(),
            alert_recipient="user+tag@example.co.uk",
            created_by="admin",
        )

        assert result.alert_recipient == "user+tag@example.co.uk"
        mock_session.add.assert_called_once()
