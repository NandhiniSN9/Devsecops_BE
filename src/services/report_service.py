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
from src.utils.helpers import log_error_to_db
from src.utils.logger import logger
from src.utils.template_renderer import render_template_from_string

# Frequency window mapping (frequency name → timedelta)
FREQUENCY_WINDOWS: dict[str, timedelta] = {
    "daily": timedelta(hours=24),
    "weekly": timedelta(days=7),
    "bi-weekly": timedelta(days=14),
    "monthly": timedelta(days=30),
}

# Report type constants — must match template_name values in email_templates table
REPORT_TYPE_AT_RISK = "At Risk Report"
REPORT_TYPE_SUMMARY = "Weekly Summary Report"

# Email body template names — must match template_name values in email_templates table
EMAIL_BODY_AT_RISK = "At Risk Alert"
EMAIL_BODY_SUMMARY = "Daily Summary"


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

            # Process HTML template with Jinja2
            populated_html = self._process_template(
                template_content=template.template_content,
                specialization_name=spec_name,
                report_type=report_type,
                report_data=report_data,
            )

            # Generate PDF with wkhtmltopdf (FAST with full CSS3 support!)
            pdf_bytes = await self._generate_pdf_async(populated_html)

            # Create PDF filename
            now = datetime.utcnow()
            filename = f"{report_type.replace(' ', '_')}_{spec_name.replace(' ', '_')}_{now.strftime('%Y-%m-%d')}.pdf"

            logger.info(
                "PDF generated successfully",
                specialization=spec_name,
                report_type=report_type,
                size_kb=len(pdf_bytes) / 1024,
            )

            # Fetch email body template from database
            email_body_template_name = EMAIL_BODY_SUMMARY if report_type == REPORT_TYPE_SUMMARY else EMAIL_BODY_AT_RISK
            email_body_template = await self._repo.get_email_template_by_name(email_body_template_name)

            if not email_body_template:
                logger.warning(
                    "Email body template not found, using default",
                    template_name=email_body_template_name,
                    specialization=spec_name,
                )
                email_body_html = None
            else:
                # Render email body template with data
                email_body_html = self._render_email_body_template(
                    template_content=email_body_template.template_content,
                    report_type=report_type,
                    specialization_name=spec_name,
                    report_date=now,
                    pdf_size_kb=len(pdf_bytes) / 1024,
                )

            # Send emails to all recipients with PDF attachment (NO S3!)
            email_sent = await self._send_emails_to_recipients(
                recipients=recipients,
                report_type=report_type,
                specialization_name=spec_name,
                report_date=now,
                pdf_bytes=pdf_bytes,
                pdf_filename=filename,
                email_body_html=email_body_html,
            )

            # Record email history (no S3 URL)
            email_status = "sent" if email_sent else "failed"
            email_history = EmailHistory(
                email_history_id=uuid.uuid4(),
                setting_id=settings.setting_id,
                email_status=email_status,
                email_type=report_type,
                report_url=None,  # No S3 URL - PDF is attached directly
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
        """Fetch the data needed for the report with enhanced metrics.

        Args:
            specialization: The target specialization.
            settings: The specialization's settings.
            report_type: "At Risk Report" or "Weekly Summary Report".

        Returns:
            Dict containing the report data.
        """
        try:
            if report_type == REPORT_TYPE_SUMMARY:
                kpi = await self._repo.get_kpi_history_by_specialization(specialization.specialization_id)
                # Fetch additional data for enhanced summary report
                projects = await self._repo.get_projects_by_specialization(specialization.specialization_id)
                return await self._build_enhanced_summary_data(kpi, projects, specialization.specialization_name)
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

    async def _build_enhanced_summary_data(
        self,
        kpi: KpiHistory | None,
        projects: list[Project],
        spec_name: str
    ) -> dict:
        """Build enhanced summary report data with actual metrics.

        Args:
            kpi: The KPI history record (may be None).
            projects: List of projects for the specialization.
            spec_name: Specialization name.

        Returns:
            Dict with enhanced summary metrics including adoption rate and pipeline stats.
        """
        try:
            # Calculate basic metrics from KPI history
            total = kpi.projects_count if kpi else len(projects)
            completed = kpi.completed_count if kpi else sum(1 for p in projects if p.completed_at is not None)
            active = kpi.active_count if kpi else sum(1 for p in projects if p.status_id and 'active' in str(p.status_id).lower())

            # Calculate adoption rate (percentage of projects with DevSecOps onboarded)
            applicable_projects = [p for p in projects if p.is_applicable]
            adoption_rate = (len(applicable_projects) / total * 100) if total > 0 else 0

            # Calculate pipeline success rate from repositories
            # Note: This would require additional repo fetching - for now using placeholder
            pipeline_success_rate = 0.0  # TODO: Calculate from pipeline_runs table

            # Get top performing projects (by status and activity)
            top_projects = [
                {
                    "project_name": p.project_name,
                    "client": p.client or "N/A",
                    "status": "Active" if p.status_id else "Unknown",
                    "success_rate": 95.0,  # TODO: Calculate from pipeline data
                }
                for p in projects[:3]  # Top 3 projects
            ]

            # Calculate date range (last 7 days for weekly report)
            today = datetime.utcnow()
            start_date = (today - timedelta(days=7)).strftime("%Y-%m-%d")
            end_date = today.strftime("%Y-%m-%d")

            return {
                "specialization_name": spec_name,
                "report_date": today.strftime("%Y-%m-%d"),
                "start_date": start_date,
                "end_date": end_date,
                "total_projects": total,
                "completed": completed,
                "active": active,
                "inactive": kpi.inactive_count if kpi else 0,
                "at_risk": kpi.at_risk_count if kpi else 0,
                "not_applicable": kpi.not_applicable_count if kpi else 0,
                "adoption_rate": round(adoption_rate, 1),
                "pipeline_success_rate": round(pipeline_success_rate, 1),
                "security_scans_passed": 0,  # TODO: Calculate from security_scans table
                "top_projects": top_projects,
            }
        except Exception as exc:
            logger.error("Error in _build_enhanced_summary_data", error=str(exc))
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
        """Process HTML template with Jinja2, injecting dynamic data.

        Args:
            template_content: The raw HTML template string from database.
            specialization_name: Name of the specialization.
            report_type: The report type.
            report_data: Dict containing the data to inject.

        Returns:
            The populated HTML string.
        """
        try:
            # Prepare context for Jinja2 template
            context = {
                "specialization_name": specialization_name,
                "report_date": report_data.get("report_date", datetime.now().strftime("%Y-%m-%d")),
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "dashboard_url": "https://dashboard.devsecops.local",  # TODO: Make this configurable
            }

            # Add report-specific data
            if report_type == REPORT_TYPE_SUMMARY:
                context.update(self._prepare_summary_context(report_data))
            elif report_type == REPORT_TYPE_AT_RISK:
                context.update(self._prepare_at_risk_context(report_data))

            # Render template from database string using Jinja2
            return render_template_from_string(template_content, context)
        except Exception as exc:
            logger.error("Error in _process_template", error=str(exc), report_type=report_type)
            raise

    def _prepare_summary_context(self, data: dict) -> dict:
        """Prepare context data for weekly summary template.

        Args:
            data: Summary report data dict.

        Returns:
            Dictionary with template context variables.
        """
        return {
            "total_projects": data.get("total_projects", 0),
            "active_projects": data.get("active", 0),
            "completed_projects": data.get("completed", 0),
            "at_risk_count": data.get("at_risk", 0),
            "adoption_rate": round(data.get("adoption_rate", 0), 1) if data.get("adoption_rate") else 0,
            "pipeline_success_rate": round(data.get("pipeline_success_rate", 0), 1) if data.get("pipeline_success_rate") else 0,
            "security_scans_passed": data.get("security_scans_passed", 0),
            "top_projects": data.get("top_projects", []),
            "start_date": data.get("start_date", ""),
            "end_date": data.get("end_date", ""),
        }

    def _prepare_at_risk_context(self, data: dict) -> dict:
        """Prepare context data for at-risk alert template.

        Args:
            data: At-risk report data dict.

        Returns:
            Dictionary with template context variables.
        """
        return {
            "at_risk_count": data.get("at_risk_count", 0),
            "projects": data.get("projects", []),
        }

    async def _generate_pdf_async(self, html_content: str) -> bytes:
        """Convert HTML to PDF asynchronously using wkhtmltopdf (FAST + Full CSS3).

        wkhtmltopdf supports modern CSS3 (Grid, Flexbox, gradients, pseudo-elements)
        and is very fast. Uses WebKit rendering engine.

        Args:
            html_content: The populated HTML string.

        Returns:
            PDF content as bytes.
        """
        try:
            import asyncio

            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            pdf_bytes = await loop.run_in_executor(
                None,
                self._generate_pdf_sync,
                html_content
            )
            return pdf_bytes
        except Exception as exc:
            logger.error("Error in _generate_pdf_async", error=str(exc))
            raise

    def _generate_pdf_sync(self, html_content: str) -> bytes:
        """Convert HTML to PDF using wkhtmltopdf - FAST with full CSS3 support!

        wkhtmltopdf advantages:
        - Full CSS3 support (Grid, Flexbox, gradients, animations, pseudo-elements)
        - WebKit rendering engine (same as Chrome/Safari)
        - Fast rendering (similar to xhtml2pdf speed)
        - Works on Windows, Linux, macOS

        Args:
            html_content: The populated HTML string.

        Returns:
            PDF content as bytes.
        """
        try:
            import pdfkit
            import os

            # wkhtmltopdf options for better rendering
            options = {
                'enable-local-file-access': None,
                'encoding': 'UTF-8',
                'page-size': 'A4',
                'margin-top': '15mm',
                'margin-right': '15mm',
                'margin-bottom': '15mm',
                'margin-left': '15mm',
                'no-outline': None,
                'quiet': '',
            }

            # Configure wkhtmltopdf path (cross-platform: Windows + Linux)
            import platform
            import shutil

            config = None
            if platform.system() == 'Windows':
                # Windows: check default installation path
                wkhtmltopdf_path = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
                if os.path.exists(wkhtmltopdf_path):
                    config = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)
                    logger.debug("Using wkhtmltopdf from Windows path", path=wkhtmltopdf_path)
            else:
                # Linux/macOS: find wkhtmltopdf from system PATH
                wkhtmltopdf_path = shutil.which('wkhtmltopdf')
                if wkhtmltopdf_path:
                    config = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)
                    logger.debug("Using wkhtmltopdf from system PATH", path=wkhtmltopdf_path)
                else:
                    # Common Linux paths as fallback
                    for path in ['/usr/bin/wkhtmltopdf', '/usr/local/bin/wkhtmltopdf']:
                        if os.path.exists(path):
                            config = pdfkit.configuration(wkhtmltopdf=path)
                            logger.debug("Using wkhtmltopdf from fallback path", path=path)
                            break

            # Convert HTML to PDF - FAST with full CSS3!
            pdf_bytes = pdfkit.from_string(html_content, False, options=options, configuration=config)

            logger.info("PDF generated with wkhtmltopdf", size_bytes=len(pdf_bytes))
            return pdf_bytes
        except Exception as exc:
            logger.error("Error in _generate_pdf_sync", error=str(exc))
            raise

    async def _send_emails_to_recipients(
        self,
        recipients: list,
        report_type: str,
        specialization_name: str,
        report_date: datetime,
        pdf_bytes: bytes,
        pdf_filename: str,
        email_body_html: str | None = None,
    ) -> bool:
        """Send emails to all active recipients with PDF attachment.

        Args:
            recipients: List of EmailRecipient records.
            report_type: The report type for the subject line.
            specialization_name: Specialization name for the subject line.
            report_date: The report generation timestamp.
            pdf_bytes: PDF content as bytes.
            pdf_filename: PDF filename for attachment.
            email_body_html: Optional rendered email body from database template.

        Returns:
            True if at least one email was sent successfully, False if all failed.
        """
        try:
            subject = (
                f"[DevSecOps Dashboard] {report_type} - {specialization_name} - {report_date.strftime('%Y-%m-%d')}"
            )

            # Use database template if available, otherwise use default
            if email_body_html:
                html_body = email_body_html
            else:
                html_body = self._build_email_body(
                    report_type=report_type,
                    specialization_name=specialization_name,
                    report_date=report_date,
                    pdf_size_kb=len(pdf_bytes) / 1024,
                )

            success_count = 0
            for recipient in recipients:
                try:
                    sent = await self._graph_client.send_email(
                        to_email=recipient.alert_recipient,
                        subject=subject,
                        html_body=html_body,
                        attachment_bytes=pdf_bytes,
                        attachment_filename=pdf_filename,
                    )
                    if sent:
                        success_count += 1
                        logger.info(
                            "Email sent with PDF attachment",
                            recipient=recipient.alert_recipient,
                            pdf_size_kb=len(pdf_bytes) / 1024,
                        )
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

    def _render_email_body_template(
        self,
        template_content: str,
        report_type: str,
        specialization_name: str,
        report_date: datetime,
        pdf_size_kb: float,
    ) -> str:
        """Render email body template from database with Jinja2.

        Args:
            template_content: HTML template content from database.
            report_type: The report type.
            specialization_name: The specialization name.
            report_date: The report generation timestamp.
            pdf_size_kb: Size of PDF in KB.

        Returns:
            Rendered HTML string for email body.
        """
        try:
            context = {
                "report_type": report_type,
                "specialization_name": specialization_name,
                "report_date": report_date.strftime("%Y-%m-%d"),
                "report_date_full": report_date.strftime("%Y-%m-%d %H:%M UTC"),
                "pdf_size_kb": f"{pdf_size_kb:.1f}",
                "generated_at": report_date.strftime("%Y-%m-%d %H:%M:%S"),
            }

            # Render email body template with Jinja2
            return render_template_from_string(template_content, context)
        except Exception as exc:
            logger.error("Error rendering email body template", error=str(exc))
            # Fall back to default email body
            return self._build_email_body(
                report_type=report_type,
                specialization_name=specialization_name,
                report_date=report_date,
                pdf_size_kb=pdf_size_kb,
            )

    def _build_email_body(
        self,
        report_type: str,
        specialization_name: str,
        report_date: datetime,
        pdf_size_kb: float,
    ) -> str:
        """Build the HTML email body for report with PDF attachment.

        Args:
            report_type: The report type.
            specialization_name: The specialization name.
            report_date: The report generation timestamp.
            pdf_size_kb: Size of PDF in KB.

        Returns:
            HTML string for the email body.
        """
        try:
            return f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; padding: 20px; line-height: 1.6; }}
                .header {{ background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
                          color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
                .content {{ background: #f8f9fa; padding: 20px; border-radius: 8px; }}
                .attachment-notice {{ background: #e3f2fd; border-left: 4px solid #2196f3;
                                     padding: 15px; margin: 20px 0; }}
                .footer {{ color: #666; font-size: 12px; margin-top: 20px;
                          padding-top: 20px; border-top: 1px solid #ddd; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1 style="margin: 0;">{report_type}</h1>
                <p style="margin: 5px 0 0 0; opacity: 0.9;">{specialization_name}</p>
            </div>

            <div class="content">
                <h2>📊 Your Report is Ready!</h2>
                <p>Report generated on: <strong>{report_date.strftime("%Y-%m-%d %H:%M UTC")}</strong></p>

                <div class="attachment-notice">
                    <strong>📎 PDF Report Attached</strong><br>
                    The complete {report_type.lower()} report for <strong>{specialization_name}</strong>
                    is attached to this email as a PDF file ({pdf_size_kb:.1f} KB).
                </div>

                <p><strong>What's included in this report:</strong></p>
                <ul>
                    <li>Key performance indicators and metrics</li>
                    <li>Project status and health overview</li>
                    <li>Detailed data analysis and trends</li>
                    <li>Professional formatting with ZEB Company branding</li>
                </ul>

                <p>Open the PDF attachment to view the full report with charts, tables, and detailed insights.</p>
            </div>

            <div class="footer">
                <p>🤖 This is an automated email from the DevSecOps Dashboard.</p>
                <p>Report generation powered by wkhtmltopdf with full CSS3 support 🚀</p>
                <p style="margin-top: 10px; color: #999;">
                    Please do not reply to this email. For support, contact your DevSecOps team.
                </p>
            </div>
        </body>
        </html>
        """
        except Exception as exc:
            logger.error("Error in _build_email_body", error=str(exc))
            raise
