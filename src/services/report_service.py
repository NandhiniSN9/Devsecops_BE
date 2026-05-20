"""Report generation and email delivery service.

Orchestrates the full pipeline: specialization iteration, frequency evaluation,
template processing, PDF generation, S3 upload, email delivery, and history tracking.
Uses Microsoft Graph API for email delivery and WeasyPrint for PDF generation.
"""

import asyncio
import traceback
import uuid
from datetime import date, datetime, timedelta
from io import BytesIO
from bs4 import BeautifulSoup
from src.client.graph_client import GraphClient
from src.client.s3_client import S3Client
from src.repositories.report_repository import ReportRepository
from src.repositories.schema.cron_job import CronJob
from src.repositories.schema.email_history import EmailHistory
from src.repositories.schema.kpi_history import KpiHistory
from src.repositories.schema.project import Project
from src.repositories.schema.setting import Setting
from src.repositories.schema.specialization import Specialization
from src.settings import REPORT_SERVICE_IDENTIFIER
from src.utils.logger import logger

# Frequency window mapping (frequency name → timedelta)
FREQUENCY_WINDOWS: dict[str, timedelta] = {
    "daily": timedelta(hours=24),
    "weekly": timedelta(days=7),
    "bi-weekly": timedelta(days=14),
    "monthly": timedelta(days=30),
}

# Report type constants — must match template_name values in email_templates table
REPORT_TYPE_AT_RISK = "At Risk Alert"
REPORT_TYPE_SUMMARY = "Weekly Digest"


class ReportService:
    """Service for generating PDF reports and sending email notifications.

    Handles the complete report generation pipeline per specialization:
    frequency evaluation, data retrieval, HTML template processing,
    PDF generation, S3 upload, and email delivery via Graph API.
    """

    def __init__(
        self,
        report_repo: ReportRepository,
        graph_client: GraphClient,
        s3_client: S3Client,
    ) -> None:
        """Initialize with dependencies.

        Args:
            report_repo: Repository for database operations.
            graph_client: Microsoft Graph API client for email delivery.
            s3_client: AWS S3 client for PDF upload.
        """
        self._repo = report_repo
        self._graph_client = graph_client
        self._s3_client = s3_client

    async def generate_reports(self) -> dict:
        """Generate and send reports for all active specializations.

        Iterates over all active specializations, evaluates frequency settings,
        generates PDF reports, uploads to S3, and sends emails to recipients.

        Returns:
            Dict with processing summary.
        """
        try:
            specializations = await self._repo.get_active_specializations()
            logger.info("Starting report generation", specialization_count=len(specializations))

            for specialization in specializations:
                await self._process_specialization(specialization)

            logger.info("Report generation completed for all specializations")
            return {"status": "completed", "specializations_processed": len(specializations)}
        except Exception as exc:
            logger.error("Error in generate_reports", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="generate_reports",
                error_file="src/services/report_service.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def _process_specialization(self, specialization: Specialization) -> None:
        """Process report generation for a single specialization.

        Creates a cron job record, evaluates frequency for both report types,
        and generates/sends reports that are due.

        Args:
            specialization: The specialization to process.
        """
        spec_name = specialization.specialization_name
        spec_id = specialization.specialization_id

        # Create cron job record
        cron_job = CronJob(
            cron_id=uuid.uuid4(),
            type="email",
            sync_status="pending",
            created_at=datetime.utcnow(),
            created_by=REPORT_SERVICE_IDENTIFIER,
        )
        await self._repo.create_cron_job(cron_job)

        try:
            # Fetch settings for this specialization
            settings = await self._repo.get_settings_by_specialization_id(spec_id)
            if not settings:
                logger.warning("No settings found for specialization", specialization=spec_name)
                await self._repo.update_cron_job_status(cron_job.cron_id, "fail")
                return

            # Process both report types
            report_configs = [
                (REPORT_TYPE_SUMMARY, settings.email_digest),
                (REPORT_TYPE_AT_RISK, settings.at_risk_alert),
            ]

            any_report_sent = False
            for report_type, frequency in report_configs:
                sent = await self._process_report_type(
                    specialization=specialization,
                    settings=settings,
                    report_type=report_type,
                    frequency=frequency,
                )
                if sent:
                    any_report_sent = True

            # Update cron job status — success even if no reports were due
            # (the cron executed without errors)
            await self._repo.update_cron_job_status(cron_job.cron_id, "success")
            logger.info(
                "Specialization processing completed",
                specialization=spec_name,
                reports_sent=any_report_sent,
            )

        except Exception as exc:
            logger.error(
                "Error processing specialization",
                specialization=spec_name,
                error=str(exc),
            )
            await self._repo.update_cron_job_status(cron_job.cron_id, "fail")
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="_process_specialization",
                error_file="src/services/report_service.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def _process_report_type(
        self,
        specialization: Specialization,
        settings: Setting,
        report_type: str,
        frequency: str | None,
    ) -> bool:
        """Process a single report type for a specialization.

        Evaluates frequency, generates PDF, uploads, and sends email.

        Args:
            specialization: The target specialization.
            settings: The specialization's settings record.
            report_type: "At-risk" or "Summary report".
            frequency: The configured frequency string.

        Returns:
            True if the report was sent, False if skipped.
        """
        try:
            spec_name = specialization.specialization_name

            # Check if report is required
            if not frequency or frequency == "not_required":
                logger.debug(
                    "Report type not required, skipping",
                    specialization=spec_name,
                    report_type=report_type,
                )
                return False

            # Evaluate frequency window
            if not await self._is_report_due(settings.setting_id, report_type, frequency):
                logger.debug(
                    "Report already sent within frequency window, skipping",
                    specialization=spec_name,
                    report_type=report_type,
                    frequency=frequency,
                )
                return False

            # Fetch recipients
            recipients = await self._repo.get_active_recipients_by_specialization(specialization.specialization_id)
            if not recipients:
                logger.warning(
                    "No active recipients configured, skipping specialization",
                    specialization=spec_name,
                    report_type=report_type,
                )
                return False

            # Fetch email template
            template = await self._repo.get_email_template_by_name(report_type)
            if not template:
                logger.error(
                    "Email template not found",
                    template_name=report_type,
                    specialization=spec_name,
                )
                raise RuntimeError(f"Email template not found: {report_type}")

            # Fetch report data
            report_data = await self._fetch_report_data(specialization, settings, report_type)

            # Process HTML template with BeautifulSoup
            populated_html = self._process_template(
                template_content=template.template_content,
                specialization_name=spec_name,
                report_type=report_type,
                report_data=report_data,
            )

            # Generate PDF with WeasyPrint (in-memory)
            pdf_bytes = self._generate_pdf(populated_html)

            # Upload to S3 and get pre-signed URL
            # NOTE: S3 upload temporarily disabled for local testing.
            # Uncomment the block below when S3 bucket is configured.
            now = datetime.utcnow()
            filename = f"{report_type}_{spec_name}_{now.strftime('%Y%m%d_%H%M%S')}.pdf"
            s3_key = f"reports/{spec_name}/{report_type}/{now.strftime('%Y')}/{now.strftime('%m')}/{filename}"

            try:
                await self._s3_client.upload_pdf(pdf_bytes, s3_key)
                presigned_url = await self._s3_client.generate_presigned_url(s3_key)
            except Exception as s3_exc:
                logger.warning(
                    "S3 upload failed, using placeholder URL for email",
                    error=str(s3_exc),
                    specialization=spec_name,
                )
                presigned_url = f"https://placeholder-report-url.local/{s3_key}"

            # Send emails to all recipients
            email_sent = await self._send_emails_to_recipients(
                recipients=recipients,
                report_type=report_type,
                specialization_name=spec_name,
                report_url=presigned_url,
                report_date=now,
            )

            # Record email history
            email_status = "sent" if email_sent else "failed"
            email_history = EmailHistory(
                email_history_id=uuid.uuid4(),
                setting_id=settings.setting_id,
                email_status=email_status,
                email_type=report_type,
                report_url=presigned_url if email_sent else None,
                last_synced=now,
                created_at=now,
                created_by=REPORT_SERVICE_IDENTIFIER,
                is_active=1,
            )
            await self._repo.create_email_history(email_history)

            logger.info(
                "Report processed",
                specialization=spec_name,
                report_type=report_type,
                email_status=email_status,
                recipients_count=len(recipients),
            )

            return email_sent
        except Exception as exc:
            logger.error("Error in _process_report_type", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="_process_report_type",
                error_file="src/services/report_service.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def _is_report_due(self, setting_id: uuid.UUID, email_type: str, frequency: str) -> bool:
        """Evaluate whether a report should be sent based on frequency window.

        Args:
            setting_id: The settings record UUID.
            email_type: The report type.
            frequency: The frequency string (daily, weekly, bi-weekly, monthly).

        Returns:
            True if the report is due, False if already sent within the window.
        """
        try:
            window = FREQUENCY_WINDOWS.get(frequency)
            if not window:
                return False

            last_history = await self._repo.get_last_sent_email_history(setting_id, email_type)
            if not last_history or not last_history.last_synced:
                # No history exists — report is due immediately
                return True

            elapsed = datetime.utcnow() - last_history.last_synced
            return elapsed >= window
        except Exception as exc:
            logger.error("Error in _is_report_due", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="_is_report_due",
                error_file="src/services/report_service.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def _fetch_report_data(
        self,
        specialization: Specialization,
        settings: Setting,
        report_type: str,
    ) -> dict:
        """Fetch the data needed for the report.

        Args:
            specialization: The target specialization.
            settings: The specialization's settings.
            report_type: "At-risk" or "Summary report".

        Returns:
            Dict containing the report data.
        """
        try:
            if report_type == REPORT_TYPE_SUMMARY:
                kpi = await self._repo.get_kpi_history_by_specialization(specialization.specialization_id)
                return self._build_summary_data(kpi, specialization.specialization_name)
            else:
                projects = await self._repo.get_at_risk_projects(settings.at_risk_threshold)
                return self._build_at_risk_data(projects, specialization.specialization_name, settings.at_risk_threshold)
        except Exception as exc:
            logger.error("Error in _fetch_report_data", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="_fetch_report_data",
                error_file="src/services/report_service.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    def _build_summary_data(self, kpi: KpiHistory | None, spec_name: str) -> dict:
        """Build summary report data from KPI history.

        Args:
            kpi: The KPI history record (may be None).
            spec_name: Specialization name.

        Returns:
            Dict with summary metrics.
        """
        try:
            if not kpi:
                return {
                    "specialization_name": spec_name,
                    "report_date": datetime.utcnow().strftime("%Y-%m-%d"),
                    "total_projects": 0,
                    "completed": 0,
                    "active": 0,
                    "inactive": 0,
                    "at_risk": 0,
                    "not_applicable": 0,
                }

            total = kpi.projects_count or 0
            return {
                "specialization_name": spec_name,
                "report_date": datetime.utcnow().strftime("%Y-%m-%d"),
                "total_projects": total,
                "completed": kpi.completed_count or 0,
                "active": kpi.active_count or 0,
                "inactive": kpi.inactive_count or 0,
                "at_risk": kpi.at_risk_count or 0,
                "not_applicable": kpi.not_applicable_count or 0,
            }
        except Exception as exc:
            logger.error("Error in _build_summary_data", error=str(exc))
            raise

    def _build_at_risk_data(self, projects: list[Project], spec_name: str, threshold: int) -> dict:
        """Build at-risk report data from project records.

        Args:
            projects: List of at-risk projects.
            spec_name: Specialization name.
            threshold: The at-risk threshold in days.

        Returns:
            Dict with at-risk project details.
        """
        try:

            project_list = []
            today = date.today()
            for project in projects:
                days_overdue = (today - project.onboarded_date).days - threshold
                project_list.append(
                    {
                        "project_name": project.project_name,
                        "client": project.client or "N/A",
                        "onboarded_date": project.onboarded_date.isoformat(),
                        "days_overdue": max(days_overdue, 0),
                    }
                )

            return {
                "specialization_name": spec_name,
                "report_date": datetime.utcnow().strftime("%Y-%m-%d"),
                "at_risk_count": len(project_list),
                "projects": project_list,
            }
        except Exception as exc:
            logger.error("Error in _build_at_risk_data", error=str(exc))
            raise

    def _process_template(
        self,
        template_content: str,
        specialization_name: str,
        report_type: str,
        report_data: dict,
    ) -> str:
        """Process HTML template with BeautifulSoup, injecting dynamic data.

        Args:
            template_content: The raw HTML template string.
            specialization_name: Name of the specialization.
            report_type: The report type.
            report_data: Dict containing the data to inject.

        Returns:
            The populated HTML string.
        """
        try:
            soup = BeautifulSoup(template_content, "html.parser")

            # Inject specialization name
            spec_elem = soup.find(id="specialization-name")
            if spec_elem:
                spec_elem.string = specialization_name

            # Inject report date
            date_elem = soup.find(id="report-date")
            if date_elem:
                date_elem.string = report_data.get("report_date", "")

            if report_type == REPORT_TYPE_SUMMARY:
                self._inject_summary_data(soup, report_data)
            else:
                self._inject_at_risk_data(soup, report_data)

            return str(soup)
        except Exception as exc:
            logger.error("Error in _process_template", error=str(exc))
            raise

    def _inject_summary_data(self, soup: BeautifulSoup, data: dict) -> None:
        """Inject summary report data into the HTML template.

        Args:
            soup: The BeautifulSoup parsed HTML.
            data: Summary report data dict.
        """
        try:
            field_mapping = {
                "total-projects": "total_projects",
                "completed-count": "completed",
                "active-count": "active",
                "inactive-count": "inactive",
                "at-risk-count": "at_risk",
                "not-applicable-count": "not_applicable",
            }

            for element_id, data_key in field_mapping.items():
                elem = soup.find(id=element_id)
                if elem:
                    elem.string = str(data.get(data_key, 0))
        except Exception as exc:
            logger.error("Error in _inject_summary_data", error=str(exc))
            raise

    def _inject_at_risk_data(self, soup: BeautifulSoup, data: dict) -> None:
        """Inject at-risk report data into the HTML template.

        Args:
            soup: The BeautifulSoup parsed HTML.
            data: At-risk report data dict.
        """
        try:
            # Inject at-risk count
            count_elem = soup.find(id="at-risk-count")
            if count_elem:
                count_elem.string = str(data.get("at_risk_count", 0))

            # Inject project rows into the table body
            tbody = soup.find(id="projects-table-body")
            if tbody and data.get("projects"):
                tbody.clear()
                for project in data["projects"]:
                    row = soup.new_tag("tr")

                    name_td = soup.new_tag("td")
                    name_td.string = project["project_name"]
                    row.append(name_td)

                    client_td = soup.new_tag("td")
                    client_td.string = project["client"]
                    row.append(client_td)

                    date_td = soup.new_tag("td")
                    date_td.string = project["onboarded_date"]
                    row.append(date_td)

                    overdue_td = soup.new_tag("td")
                    overdue_td.string = str(project["days_overdue"])
                    row.append(overdue_td)

                    tbody.append(row)
        except Exception as exc:
            logger.error("Error in _inject_at_risk_data", error=str(exc))
            raise

    def _generate_pdf(self, html_content: str) -> bytes:
        """Convert HTML content to PDF bytes using WeasyPrint.

        Generates the PDF entirely in memory without writing to disk.

        Args:
            html_content: The populated HTML string.

        Returns:
            PDF content as bytes.
        """
        try:
            from weasyprint import HTML

            pdf_buffer = BytesIO()
            HTML(string=html_content).write_pdf(pdf_buffer)
            pdf_bytes = pdf_buffer.getvalue()
            pdf_buffer.close()
            logger.info("PDF generated in memory", size_bytes=len(pdf_bytes))
            return pdf_bytes
        except Exception as exc:
            logger.error("Error in _generate_pdf", error=str(exc))
            raise

    async def _send_emails_to_recipients(
        self,
        recipients: list,
        report_type: str,
        specialization_name: str,
        report_url: str,
        report_date: datetime,
    ) -> bool:
        """Send emails to all active recipients with skip-and-continue pattern.

        Args:
            recipients: List of EmailRecipient records.
            report_type: The report type for the subject line.
            specialization_name: Specialization name for the subject line.
            report_url: The pre-signed URL to the PDF report.
            report_date: The report generation timestamp.

        Returns:
            True if at least one email was sent successfully, False if all failed.
        """
        try:
            subject = (
                f"[DevSecOps Dashboard] {report_type} Report - {specialization_name} - {report_date.strftime('%Y-%m-%d')}"
            )

            html_body = self._build_email_body(
                report_type=report_type,
                specialization_name=specialization_name,
                report_url=report_url,
                report_date=report_date,
            )

            success_count = 0
            for recipient in recipients:
                try:
                    sent = await self._graph_client.send_email(
                        to_email=recipient.alert_recipient,
                        subject=subject,
                        html_body=html_body,
                    )
                    if sent:
                        success_count += 1
                except Exception as exc:
                    logger.warning(
                        "Failed to send email to recipient",
                        recipient=recipient.alert_recipient,
                        error=str(exc),
                    )

            logger.info(
                "Email delivery completed",
                total_recipients=len(recipients),
                successful=success_count,
                failed=len(recipients) - success_count,
            )

            return success_count > 0
        except Exception as exc:
            logger.error("Error in _send_emails_to_recipients", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="_send_emails_to_recipients",
                error_file="src/services/report_service.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    def _build_email_body(
        self,
        report_type: str,
        specialization_name: str,
        report_url: str,
        report_date: datetime,
    ) -> str:
        """Build the HTML email body with the report download link.

        Args:
            report_type: The report type.
            specialization_name: The specialization name.
            report_url: The pre-signed URL to the PDF.
            report_date: The report generation timestamp.

        Returns:
            HTML string for the email body.
        """
        try:
            return f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2>{report_type} Report - {specialization_name}</h2>
            <p>Report generated on: <strong>{report_date.strftime("%Y-%m-%d %H:%M UTC")}</strong></p>
            <p>Your {report_type.lower()} report for the <strong>{specialization_name}</strong>
            specialization is ready for download.</p>
            <p>
                <a href="{report_url}"
                   style="background-color: #0078D4; color: white; padding: 10px 20px;
                          text-decoration: none; border-radius: 4px; display: inline-block;">
                    Download Report (PDF)
                </a>
            </p>
            <p style="color: #666; font-size: 12px;">
                This link will expire in 7 days. Please download the report before expiration.
            </p>
            <hr style="border: none; border-top: 1px solid #eee; margin-top: 20px;">
            <p style="color: #999; font-size: 11px;">
                This is an automated email from the DevSecOps Dashboard.
                Please do not reply to this email.
            </p>
        </body>
        </html>
        """
        except Exception as exc:
            logger.error("Error in _build_email_body", error=str(exc))
            raise
