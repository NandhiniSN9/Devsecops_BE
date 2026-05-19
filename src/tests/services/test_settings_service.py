"""Unit tests for SettingsService business logic."""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.models.request.settings_request import EmailRecipientAction, SettingsUpdateRequest
from src.repositories.settings_repository import SettingsRepository
from src.services.settings_service import SettingsService
from src.utils.exceptions import InvalidParameterError, NotFoundError


@pytest.fixture
def mock_settings_repo():
    """Create a mock SettingsRepository."""
    repo = AsyncMock(spec=SettingsRepository)
    repo.commit = AsyncMock()
    return repo


@pytest.fixture
def service(mock_settings_repo):
    """Create a SettingsService with mocked repository."""
    return SettingsService(settings_repo=mock_settings_repo)


def _make_specialization(spec_id=None, name="Backend"):
    """Helper to create a mock specialization."""
    spec = MagicMock()
    spec.specialization_id = spec_id or uuid.uuid4()
    spec.specialization_name = name
    return spec


def _make_setting(setting_id=None, spec_id=None):
    """Helper to create a mock setting record."""
    setting = MagicMock()
    setting.setting_id = setting_id or uuid.uuid4()
    setting.specialization_id = spec_id or uuid.uuid4()
    setting.at_risk_threshold = 5
    setting.email_digest = "weekly"
    setting.at_risk_alert = "daily"
    setting.last_synced = None
    return setting


def _make_recipient(recipient_id=None, email="test@company.com"):
    """Helper to create a mock email recipient."""
    recipient = MagicMock()
    recipient.email_recipient_id = recipient_id or uuid.uuid4()
    recipient.alert_recipient = email
    return recipient


class TestGetSettings:
    """Tests for SettingsService.get_settings."""

    @pytest.mark.asyncio
    async def test_returns_settings_data(self, service, mock_settings_repo):
        """Should return settings with recipients for a valid specialization."""
        spec_id = uuid.uuid4()
        spec = _make_specialization(spec_id, "Backend")
        setting = _make_setting(spec_id=spec_id)
        recipients = [_make_recipient(email="lead@company.com")]

        mock_settings_repo.get_specialization.return_value = spec
        mock_settings_repo.get_settings_by_specialization.return_value = setting
        mock_settings_repo.get_email_recipients.return_value = recipients

        result = await service.get_settings(str(spec_id))

        assert result.specialization_name == "Backend"
        assert result.at_risk_threshold == 5
        assert len(result.email_recipients) == 1
        assert result.email_recipients[0].alert_recipient == "lead@company.com"

    @pytest.mark.asyncio
    async def test_invalid_uuid_raises_error(self, service):
        """Should raise InvalidParameterError for invalid UUID format."""
        with pytest.raises(InvalidParameterError) as exc_info:
            await service.get_settings("not-a-uuid")
        assert "specializationId" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_specialization_not_found_raises_error(self, service, mock_settings_repo):
        """Should raise NotFoundError when specialization doesn't exist."""
        mock_settings_repo.get_specialization.return_value = None

        with pytest.raises(NotFoundError) as exc_info:
            await service.get_settings(str(uuid.uuid4()))
        assert "Specialization not found" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_settings_not_found_raises_error(self, service, mock_settings_repo):
        """Should raise NotFoundError when settings don't exist for specialization."""
        mock_settings_repo.get_specialization.return_value = _make_specialization()
        mock_settings_repo.get_settings_by_specialization.return_value = None

        with pytest.raises(NotFoundError) as exc_info:
            await service.get_settings(str(uuid.uuid4()))
        assert "Settings not found" in exc_info.value.message


class TestUpdateSettings:
    """Tests for SettingsService.update_settings."""

    @pytest.mark.asyncio
    async def test_updates_at_risk_threshold(self, service, mock_settings_repo):
        """Should update at_risk_threshold when provided."""
        spec_id = uuid.uuid4()
        spec = _make_specialization(spec_id)
        setting = _make_setting(spec_id=spec_id)

        mock_settings_repo.get_specialization.return_value = spec
        mock_settings_repo.get_settings_by_specialization.return_value = setting
        mock_settings_repo.get_email_recipients.return_value = []

        request = SettingsUpdateRequest(
            specialization_id=spec_id,
            at_risk_threshold=10,
        )

        await service.update_settings(request)

        mock_settings_repo.update_setting_fields.assert_called_once()
        update_fields = mock_settings_repo.update_setting_fields.call_args[0][1]
        assert update_fields["at_risk_threshold"] == 10

    @pytest.mark.asyncio
    async def test_updates_email_digest_schedule(self, service, mock_settings_repo):
        """Should update email_digest when valid schedule provided."""
        spec_id = uuid.uuid4()
        spec = _make_specialization(spec_id)
        setting = _make_setting(spec_id=spec_id)

        mock_settings_repo.get_specialization.return_value = spec
        mock_settings_repo.get_settings_by_specialization.return_value = setting
        mock_settings_repo.get_email_recipients.return_value = []

        request = SettingsUpdateRequest(
            specialization_id=spec_id,
            email_digest="daily",
        )

        await service.update_settings(request)

        update_fields = mock_settings_repo.update_setting_fields.call_args[0][1]
        assert update_fields["email_digest"] == "daily"

    @pytest.mark.asyncio
    async def test_invalid_schedule_value_raises_error(self, service, mock_settings_repo):
        """Should raise InvalidParameterError for invalid schedule value."""
        spec_id = uuid.uuid4()
        mock_settings_repo.get_specialization.return_value = _make_specialization(spec_id)
        mock_settings_repo.get_settings_by_specialization.return_value = _make_setting(spec_id=spec_id)

        request = SettingsUpdateRequest(
            specialization_id=spec_id,
            email_digest="every_hour",  # invalid
        )

        with pytest.raises(InvalidParameterError) as exc_info:
            await service.update_settings(request)
        assert "email_digest" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_add_email_recipient(self, service, mock_settings_repo):
        """Should add a new email recipient."""
        spec_id = uuid.uuid4()
        setting_id = uuid.uuid4()
        spec = _make_specialization(spec_id)
        setting = _make_setting(setting_id=setting_id, spec_id=spec_id)

        mock_settings_repo.get_specialization.return_value = spec
        mock_settings_repo.get_settings_by_specialization.return_value = setting
        mock_settings_repo.check_duplicate_recipient.return_value = False
        mock_settings_repo.get_email_recipients.return_value = []

        request = SettingsUpdateRequest(
            specialization_id=spec_id,
            email_recipients=[
                EmailRecipientAction(action="add", alert_recipient="new@company.com")
            ],
        )

        await service.update_settings(request)

        mock_settings_repo.add_email_recipient.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_duplicate_recipient_raises_error(self, service, mock_settings_repo):
        """Should raise InvalidParameterError when adding duplicate recipient."""
        spec_id = uuid.uuid4()
        spec = _make_specialization(spec_id)
        setting = _make_setting(spec_id=spec_id)

        mock_settings_repo.get_specialization.return_value = spec
        mock_settings_repo.get_settings_by_specialization.return_value = setting
        mock_settings_repo.check_duplicate_recipient.return_value = True

        request = SettingsUpdateRequest(
            specialization_id=spec_id,
            email_recipients=[
                EmailRecipientAction(action="add", alert_recipient="existing@company.com")
            ],
        )

        with pytest.raises(InvalidParameterError) as exc_info:
            await service.update_settings(request)
        assert "already exists" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_remove_email_recipient(self, service, mock_settings_repo):
        """Should soft-delete an email recipient."""
        spec_id = uuid.uuid4()
        recipient_id = uuid.uuid4()
        spec = _make_specialization(spec_id)
        setting = _make_setting(spec_id=spec_id)
        recipient = _make_recipient(recipient_id)

        mock_settings_repo.get_specialization.return_value = spec
        mock_settings_repo.get_settings_by_specialization.return_value = setting
        mock_settings_repo.get_recipient_by_id.return_value = recipient
        mock_settings_repo.get_email_recipients.return_value = []

        request = SettingsUpdateRequest(
            specialization_id=spec_id,
            email_recipients=[
                EmailRecipientAction(action="remove", email_recipient_id=recipient_id)
            ],
        )

        await service.update_settings(request)

        mock_settings_repo.soft_delete_recipient.assert_called_once()

    @pytest.mark.asyncio
    async def test_remove_nonexistent_recipient_raises_error(self, service, mock_settings_repo):
        """Should raise InvalidParameterError when removing non-existent recipient."""
        spec_id = uuid.uuid4()
        spec = _make_specialization(spec_id)
        setting = _make_setting(spec_id=spec_id)

        mock_settings_repo.get_specialization.return_value = spec
        mock_settings_repo.get_settings_by_specialization.return_value = setting
        mock_settings_repo.get_recipient_by_id.return_value = None

        request = SettingsUpdateRequest(
            specialization_id=spec_id,
            email_recipients=[
                EmailRecipientAction(action="remove", email_recipient_id=uuid.uuid4())
            ],
        )

        with pytest.raises(InvalidParameterError) as exc_info:
            await service.update_settings(request)
        assert "not found" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_add_without_email_raises_error(self, service, mock_settings_repo):
        """Should raise InvalidParameterError when adding without alert_recipient."""
        spec_id = uuid.uuid4()
        spec = _make_specialization(spec_id)
        setting = _make_setting(spec_id=spec_id)

        mock_settings_repo.get_specialization.return_value = spec
        mock_settings_repo.get_settings_by_specialization.return_value = setting

        request = SettingsUpdateRequest(
            specialization_id=spec_id,
            email_recipients=[
                EmailRecipientAction(action="add", alert_recipient=None)
            ],
        )

        with pytest.raises(InvalidParameterError) as exc_info:
            await service.update_settings(request)
        assert "alert_recipient" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_remove_without_id_raises_error(self, service, mock_settings_repo):
        """Should raise InvalidParameterError when removing without email_recipient_id."""
        spec_id = uuid.uuid4()
        spec = _make_specialization(spec_id)
        setting = _make_setting(spec_id=spec_id)

        mock_settings_repo.get_specialization.return_value = spec
        mock_settings_repo.get_settings_by_specialization.return_value = setting

        request = SettingsUpdateRequest(
            specialization_id=spec_id,
            email_recipients=[
                EmailRecipientAction(action="remove", email_recipient_id=None)
            ],
        )

        with pytest.raises(InvalidParameterError) as exc_info:
            await service.update_settings(request)
        assert "email_recipient_id" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_specialization_not_found_raises_error(self, service, mock_settings_repo):
        """Should raise NotFoundError when specialization doesn't exist."""
        mock_settings_repo.get_specialization.return_value = None

        request = SettingsUpdateRequest(specialization_id=uuid.uuid4())

        with pytest.raises(NotFoundError):
            await service.update_settings(request)
