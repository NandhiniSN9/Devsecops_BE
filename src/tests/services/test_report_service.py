"""Tests for ReportService business logic."""

import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.client.graph_client import GraphClient
from src.client.s3_client import S3Client
from src.repositories.report_repository import ReportRepository
from src.repositories.schema.email_history import EmailHistory
from src.repositories.schema.email_recipient import EmailRecipient
from src.repositories.schema.email_template import EmailTemplate
from src.repositories.schema.kpi_history import KpiHistory
from src.repositories.schema.setting import Setting
from src.repositories.schema.specialization import Specialization
from src.services.report_service import (
    REPORT_TYPE_AT_RISK,
    REPORT_TYPE_SUMMARY,
    ReportService,
)


@pytest.fixture
def mock_repo():
    """Create a mock ReportRepository."""
    repo = AsyncMock(spec=ReportRepository)
    repo.commit = AsyncMock()
    return repo


@pytest.fixture
def mock_graph_client():
    """Create a mock GraphClient."""
    client = AsyncMock(spec=GraphClient)
    client.send_email = AsyncMock(return_value=True)
    return client


@pytest.fixture
def mock_s3_client():
    """Create a mock S3Client."""
    client = AsyncMock(spec=S3Client)
    client.upload_pdf = AsyncMock(return_value="s3://bucket/key")
    client.generate_presigned_url = AsyncMock(return_value="https://s3.example.com/presigned-url")
    return client


@pytest.fixture
def service(mock_repo, mock_graph_client, mock_s3_client):
    """Create a ReportService with mocked dependencies."""
    return ReportService(
        report_repo=mock_repo,
        graph_client=mock_graph_client,
        s3_client=mock_s3_client,
    )


@pytest.fixture
def sample_specialization():
    """Create a sample specialization."""
    return Specialization(
        specialization_id=uuid.uuid4(),
        specialization_name="DevSecOps",
        is_active=1,
    )


@pytest.fixture
def sample_settings(sample_specialization):
    """Create sample settings."""
    return Setting(
        setting_id=uuid.uuid4(),
        specialization_id=sample_specialization.specialization_id,
        at_risk_threshold=30,
        email_digest="weekly",
        at_risk_alert="daily",
        is_active=1,
    )


@pytest.fixture
def sample_template():
    """Create a sample email template."""
    return EmailTemplate(
        email_template_id=uuid.uuid4(),
        template_name="Summary report",
        template_content="""
        <html>
        <body>
            <h1 id="specialization-name"></h1>
            <p id="report-date"></p>
            <span id="total-projects">0</span>
            <span id="completed-count">0</span>
            <span id="active-count">0</span>
            <span id="inactive-count">0</span>
            <span id="at-risk-count">0</span>
            <span id="not-applicable-count">0</span>
        </body>
        </html>
        """,
        is_active=1,
    )


@pytest.fixture
def sample_recipients(sample_specialization):
    """Create sample email recipients."""
    return [
        EmailRecipient(
            email_recipient_id=uuid.uuid4(),
            specialization_id=sample_specialization.specialization_id,
            alert_recipient="user1@example.com",
            is_active=1,
        ),
        EmailRecipient(
            email_recipient_id=uuid.uuid4(),
            specialization_id=sample_specialization.specialization_id,
            alert_recipient="user2@example.com",
            is_active=1,
        ),
    ]


@pytest.fixture
def sample_kpi():
    """Create sample KPI history."""
    return KpiHistory(
        kpi_history_id=uuid.uuid4(),
        projects_count=50,
        completed_count=20,
        active_count=15,
        inactive_count=5,
        at_risk_count=8,
        not_applicable_count=2,
    )


class TestGenerateReports:
    """Tests for generate_reports method."""

    @pytest.mark.asyncio
    async def test_generate_reports_no_specializations(self, service, mock_repo):
        """Should complete successfully with no active specializations."""
        mock_repo.get_active_specializations.return_value = []

        result = await service.generate_reports()

        assert result["specializations_processed"] == 0
        mock_repo.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_reports_with_specializations(
        self, service, mock_repo, sample_specialization, sample_settings, sample_template, sample_recipients, sample_kpi
    ):
        """Should process all active specializations."""
        mock_repo.get_active_specializations.return_value = [sample_specialization]
        mock_repo.get_settings_by_specialization_id.return_value = sample_settings
        mock_repo.get_last_sent_email_history.return_value = None  # No history = report is due
        mock_repo.get_email_template_by_name.return_value = sample_template
        mock_repo.get_active_recipients_by_specialization.return_value = sample_recipients
        mock_repo.get_kpi_history_by_specialization.return_value = sample_kpi
        mock_repo.create_cron_job.return_value = MagicMock()
        mock_repo.create_email_history.return_value = MagicMock()

        # Mock WeasyPrint since it requires native GTK libraries
        with patch.object(service, "_generate_pdf", return_value=b"%PDF-1.4 test"):
            result = await service.generate_reports()

        assert result["specializations_processed"] == 1
        mock_repo.commit.assert_called_once()


class TestIsReportDue:
    """Tests for _is_report_due method."""

    @pytest.mark.asyncio
    async def test_report_due_no_history(self, service, mock_repo):
        """Should return True when no history exists (first time)."""
        mock_repo.get_last_sent_email_history.return_value = None

        result = await service._is_report_due(uuid.uuid4(), "Summary report", "weekly")

        assert result is True

    @pytest.mark.asyncio
    async def test_report_due_window_elapsed(self, service, mock_repo):
        """Should return True when frequency window has elapsed."""
        old_history = EmailHistory(
            email_history_id=uuid.uuid4(),
            setting_id=uuid.uuid4(),
            email_status="sent",
            email_type="Summary report",
            last_synced=datetime.utcnow() - timedelta(days=8),  # 8 days ago, weekly window
        )
        mock_repo.get_last_sent_email_history.return_value = old_history

        result = await service._is_report_due(old_history.setting_id, "Summary report", "weekly")

        assert result is True

    @pytest.mark.asyncio
    async def test_report_not_due_within_window(self, service, mock_repo):
        """Should return False when report was sent within the window."""
        recent_history = EmailHistory(
            email_history_id=uuid.uuid4(),
            setting_id=uuid.uuid4(),
            email_status="sent",
            email_type="Summary report",
            last_synced=datetime.utcnow() - timedelta(days=2),  # 2 days ago, weekly window
        )
        mock_repo.get_last_sent_email_history.return_value = recent_history

        result = await service._is_report_due(recent_history.setting_id, "Summary report", "weekly")

        assert result is False

    @pytest.mark.asyncio
    async def test_report_due_daily_frequency(self, service, mock_repo):
        """Should return True for daily frequency after 24 hours."""
        old_history = EmailHistory(
            email_history_id=uuid.uuid4(),
            setting_id=uuid.uuid4(),
            email_status="sent",
            email_type="At-risk",
            last_synced=datetime.utcnow() - timedelta(hours=25),
        )
        mock_repo.get_last_sent_email_history.return_value = old_history

        result = await service._is_report_due(old_history.setting_id, "At-risk", "daily")

        assert result is True

    @pytest.mark.asyncio
    async def test_report_not_due_invalid_frequency(self, service, mock_repo):
        """Should return False for unknown frequency values."""
        result = await service._is_report_due(uuid.uuid4(), "Summary report", "unknown")

        assert result is False


class TestProcessTemplate:
    """Tests for _process_template method."""

    def test_process_summary_template(self, service):
        """Should inject summary data into template placeholders."""
        template = """
        <html><body>
            <h1 id="specialization-name"></h1>
            <p id="report-date"></p>
            <span id="total-projects">0</span>
            <span id="completed-count">0</span>
            <span id="active-count">0</span>
            <span id="inactive-count">0</span>
            <span id="at-risk-count">0</span>
            <span id="not-applicable-count">0</span>
        </body></html>
        """
        data = {
            "specialization_name": "DevSecOps",
            "report_date": "2026-05-15",
            "total_projects": 50,
            "completed": 20,
            "active": 15,
            "inactive": 5,
            "at_risk": 8,
            "not_applicable": 2,
        }

        result = service._process_template(template, "DevSecOps", REPORT_TYPE_SUMMARY, data)

        assert "DevSecOps" in result
        assert "2026-05-15" in result
        assert "50" in result
        assert "20" in result

    def test_process_at_risk_template(self, service):
        """Should inject at-risk project data into template."""
        template = """
        <html><body>
            <h1 id="specialization-name"></h1>
            <p id="report-date"></p>
            <span id="at-risk-count">0</span>
            <table><tbody id="projects-table-body"></tbody></table>
        </body></html>
        """
        data = {
            "specialization_name": "DevSecOps",
            "report_date": "2026-05-15",
            "at_risk_count": 2,
            "projects": [
                {
                    "project_name": "Project A",
                    "client": "Client X",
                    "onboarded_date": "2025-01-01",
                    "days_overdue": 15,
                },
            ],
        }

        result = service._process_template(template, "DevSecOps", REPORT_TYPE_AT_RISK, data)

        assert "DevSecOps" in result
        assert "Project A" in result
        assert "Client X" in result


class TestGeneratePdf:
    """Tests for _generate_pdf method."""

    def test_generate_pdf_success(self, service):
        """Should generate PDF bytes from HTML content."""
        html = "<html><body><h1>Test Report</h1><p>Content here</p></body></html>"

        with patch("src.services.report_service.BytesIO") as mock_buffer_class:
            mock_buffer = MagicMock()
            mock_buffer.getvalue.return_value = b"%PDF-1.4 test content"
            mock_buffer_class.return_value = mock_buffer

            with patch.dict("sys.modules", {"weasyprint": MagicMock()}):
                import sys

                # Create a mock weasyprint module
                mock_weasyprint = MagicMock()
                mock_html_instance = MagicMock()
                mock_weasyprint.HTML.return_value = mock_html_instance
                sys.modules["weasyprint"] = mock_weasyprint

                try:
                    result = service._generate_pdf(html)
                    assert isinstance(result, bytes)
                    assert result == b"%PDF-1.4 test content"
                    mock_weasyprint.HTML.assert_called_once_with(string=html)
                    mock_html_instance.write_pdf.assert_called_once_with(mock_buffer)
                finally:
                    del sys.modules["weasyprint"]

    def test_generate_pdf_empty_html(self, service):
        """Should handle minimal HTML gracefully."""
        html = "<html><body></body></html>"

        with patch("src.services.report_service.BytesIO") as mock_buffer_class:
            mock_buffer = MagicMock()
            mock_buffer.getvalue.return_value = b"%PDF-1.4 empty"
            mock_buffer_class.return_value = mock_buffer

            import sys

            mock_weasyprint = MagicMock()
            mock_html_instance = MagicMock()
            mock_weasyprint.HTML.return_value = mock_html_instance
            sys.modules["weasyprint"] = mock_weasyprint

            try:
                result = service._generate_pdf(html)
                assert isinstance(result, bytes)
                assert len(result) > 0
            finally:
                del sys.modules["weasyprint"]


class TestSendEmailsToRecipients:
    """Tests for _send_emails_to_recipients method."""

    @pytest.mark.asyncio
    async def test_send_emails_all_success(self, service, mock_graph_client, sample_recipients):
        """Should return True when all emails sent successfully."""
        mock_graph_client.send_email.return_value = True

        result = await service._send_emails_to_recipients(
            recipients=sample_recipients,
            report_type="Summary report",
            specialization_name="DevSecOps",
            report_url="https://example.com/report.pdf",
            report_date=datetime.utcnow(),
        )

        assert result is True
        assert mock_graph_client.send_email.call_count == 2

    @pytest.mark.asyncio
    async def test_send_emails_partial_failure(self, service, mock_graph_client, sample_recipients):
        """Should return True when at least one email succeeds."""
        mock_graph_client.send_email.side_effect = [True, False]

        result = await service._send_emails_to_recipients(
            recipients=sample_recipients,
            report_type="At-risk",
            specialization_name="DevSecOps",
            report_url="https://example.com/report.pdf",
            report_date=datetime.utcnow(),
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_send_emails_all_failed(self, service, mock_graph_client, sample_recipients):
        """Should return False when all emails fail."""
        mock_graph_client.send_email.return_value = False

        result = await service._send_emails_to_recipients(
            recipients=sample_recipients,
            report_type="Summary report",
            specialization_name="DevSecOps",
            report_url="https://example.com/report.pdf",
            report_date=datetime.utcnow(),
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_send_emails_exception_handling(self, service, mock_graph_client, sample_recipients):
        """Should handle exceptions gracefully and continue to next recipient."""
        mock_graph_client.send_email.side_effect = [Exception("Network error"), True]

        result = await service._send_emails_to_recipients(
            recipients=sample_recipients,
            report_type="Summary report",
            specialization_name="DevSecOps",
            report_url="https://example.com/report.pdf",
            report_date=datetime.utcnow(),
        )

        assert result is True


class TestBuildEmailBody:
    """Tests for _build_email_body method."""

    def test_build_email_body_contains_required_elements(self, service):
        """Should include report type, specialization, date, and download link."""
        result = service._build_email_body(
            report_type="Summary report",
            specialization_name="DevSecOps",
            report_url="https://s3.example.com/report.pdf",
            report_date=datetime(2026, 5, 15, 10, 30),
        )

        assert "Summary report" in result
        assert "DevSecOps" in result
        assert "2026-05-15" in result
        assert "https://s3.example.com/report.pdf" in result
        assert "Download Report" in result
