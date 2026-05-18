"""Tests for ReportRepository data access operations."""

import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.report_repository import ReportRepository
from src.repositories.schema.cron_job import CronJob
from src.repositories.schema.email_history import EmailHistory
from src.repositories.schema.email_recipient import EmailRecipient
from src.repositories.schema.email_template import EmailTemplate
from src.repositories.schema.setting import Setting
from src.repositories.schema.specialization import Specialization


@pytest.fixture
def mock_session():
    """Create a mock async session."""
    session = AsyncMock(spec=AsyncSession)
    return session


@pytest.fixture
def repo(mock_session):
    """Create a ReportRepository with mock session."""
    return ReportRepository(mock_session)


class TestGetActiveSpecializations:
    """Tests for get_active_specializations method."""

    @pytest.mark.asyncio
    async def test_get_active_specializations_success(self, repo, mock_session):
        """Should return list of active specializations."""
        spec = Specialization(
            specialization_id=uuid.uuid4(),
            specialization_name="DevSecOps",
            is_active=1,
        )
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [spec]
        mock_session.execute.return_value = mock_result

        result = await repo.get_active_specializations()

        assert len(result) == 1
        assert result[0].specialization_name == "DevSecOps"
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_active_specializations_empty(self, repo, mock_session):
        """Should return empty list when no active specializations exist."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        result = await repo.get_active_specializations()

        assert result == []


class TestGetSettingsBySpecializationId:
    """Tests for get_settings_by_specialization_id method."""

    @pytest.mark.asyncio
    async def test_get_settings_success(self, repo, mock_session):
        """Should return settings for a valid specialization."""
        setting = Setting(
            setting_id=uuid.uuid4(),
            specialization_id=uuid.uuid4(),
            at_risk_threshold=30,
            email_digest="weekly",
            at_risk_alert="daily",
        )
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = setting
        mock_session.execute.return_value = mock_result

        result = await repo.get_settings_by_specialization_id(setting.specialization_id)

        assert result is not None
        assert result.email_digest == "weekly"
        assert result.at_risk_alert == "daily"

    @pytest.mark.asyncio
    async def test_get_settings_not_found(self, repo, mock_session):
        """Should return None when no settings exist for specialization."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_session.execute.return_value = mock_result

        result = await repo.get_settings_by_specialization_id(uuid.uuid4())

        assert result is None


class TestGetLastSentEmailHistory:
    """Tests for get_last_sent_email_history method."""

    @pytest.mark.asyncio
    async def test_get_last_sent_history_exists(self, repo, mock_session):
        """Should return the most recent sent email history."""
        history = EmailHistory(
            email_history_id=uuid.uuid4(),
            setting_id=uuid.uuid4(),
            email_status="sent",
            email_type="Summary report",
            last_synced=datetime.utcnow() - timedelta(days=3),
        )
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = history
        mock_session.execute.return_value = mock_result

        result = await repo.get_last_sent_email_history(history.setting_id, "Summary report")

        assert result is not None
        assert result.email_status == "sent"

    @pytest.mark.asyncio
    async def test_get_last_sent_history_none(self, repo, mock_session):
        """Should return None when no sent history exists."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_session.execute.return_value = mock_result

        result = await repo.get_last_sent_email_history(uuid.uuid4(), "At-risk")

        assert result is None


class TestGetEmailTemplateByName:
    """Tests for get_email_template_by_name method."""

    @pytest.mark.asyncio
    async def test_get_template_success(self, repo, mock_session):
        """Should return template when found."""
        template = EmailTemplate(
            email_template_id=uuid.uuid4(),
            template_name="Summary report",
            template_content="<html><body>Test</body></html>",
        )
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = template
        mock_session.execute.return_value = mock_result

        result = await repo.get_email_template_by_name("Summary report")

        assert result is not None
        assert result.template_name == "Summary report"

    @pytest.mark.asyncio
    async def test_get_template_not_found(self, repo, mock_session):
        """Should return None when template doesn't exist."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_session.execute.return_value = mock_result

        result = await repo.get_email_template_by_name("Nonexistent")

        assert result is None


class TestGetActiveRecipientsBySpecialization:
    """Tests for get_active_recipients_by_specialization method."""

    @pytest.mark.asyncio
    async def test_get_recipients_success(self, repo, mock_session):
        """Should return list of active recipients."""
        recipient = EmailRecipient(
            email_recipient_id=uuid.uuid4(),
            specialization_id=uuid.uuid4(),
            alert_recipient="user@example.com",
            is_active=1,
        )
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [recipient]
        mock_session.execute.return_value = mock_result

        result = await repo.get_active_recipients_by_specialization(recipient.specialization_id)

        assert len(result) == 1
        assert result[0].alert_recipient == "user@example.com"

    @pytest.mark.asyncio
    async def test_get_recipients_empty(self, repo, mock_session):
        """Should return empty list when no recipients configured."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        result = await repo.get_active_recipients_by_specialization(uuid.uuid4())

        assert result == []


class TestCreateEmailHistory:
    """Tests for create_email_history method."""

    @pytest.mark.asyncio
    async def test_create_email_history_success(self, repo, mock_session):
        """Should persist email history record."""
        history = EmailHistory(
            email_history_id=uuid.uuid4(),
            setting_id=uuid.uuid4(),
            email_status="sent",
            email_type="At-risk",
            report_url="https://s3.example.com/report.pdf",
            last_synced=datetime.utcnow(),
            created_by="report_service",
        )

        result = await repo.create_email_history(history)

        mock_session.add.assert_called_once_with(history)
        mock_session.flush.assert_called_once()
        assert result == history


class TestCreateCronJob:
    """Tests for create_cron_job method."""

    @pytest.mark.asyncio
    async def test_create_cron_job_success(self, repo, mock_session):
        """Should persist cron job record."""
        cron_job = CronJob(
            cron_id=uuid.uuid4(),
            specialization_id=str(uuid.uuid4()),
            type="email",
            sync_status="pending",
            created_by="report_service",
        )

        result = await repo.create_cron_job(cron_job)

        mock_session.add.assert_called_once_with(cron_job)
        mock_session.flush.assert_called_once()
        assert result == cron_job


class TestUpdateCronJobStatus:
    """Tests for update_cron_job_status method."""

    @pytest.mark.asyncio
    async def test_update_cron_job_status_success(self, repo, mock_session):
        """Should update cron job status."""
        cron_id = uuid.uuid4()

        await repo.update_cron_job_status(cron_id, "success")

        mock_session.execute.assert_called_once()
        mock_session.flush.assert_called_once()
