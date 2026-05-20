"""Repository for report generation data access operations.

Provides queries for specializations, settings, email templates,
email recipients, email history, KPI data, at-risk projects,
and cron job tracking for the email notification service.
"""

import asyncio
import traceback
import uuid
from datetime import datetime
from sqlalchemy import func
from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from src.repositories.schema.cron_job import CronJob
from src.repositories.schema.email_history import EmailHistory
from src.repositories.schema.email_recipient import EmailRecipient
from src.repositories.schema.email_template import EmailTemplate
from src.repositories.schema.kpi_history import KpiHistory
from src.repositories.schema.project import Project
from src.repositories.schema.setting import Setting
from src.repositories.schema.specialization import Specialization
from src.utils.logger import logger


class ReportRepository:
    """Data access layer for report generation operations."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_active_specializations(self) -> list[Specialization]:
        """Fetch all active specializations.

        Returns:
            List of active Specialization records.
        """
        try:
            stmt = select(Specialization).where(Specialization.is_active == 1)
            result = await self._session.execute(stmt)
            return list(result.scalars().all())
        except SQLAlchemyError as db_exc:
            logger.error("Database error in get_active_specializations", error=str(db_exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(db_exc),
                error_function="get_active_specializations",
                error_file="src/repositories/report_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise
        except Exception as exc:
            logger.error("Unexpected error in get_active_specializations", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="get_active_specializations",
                error_file="src/repositories/report_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def get_settings_by_specialization_id(self, specialization_id: uuid.UUID) -> Setting | None:
        """Fetch the settings record for a given specialization.

        Args:
            specialization_id: The specialization UUID.

        Returns:
            The Setting record, or None if not found.
        """
        try:
            stmt = select(Setting).where(
                Setting.specialization_id == specialization_id,
                Setting.is_active == 1,
            )
            result = await self._session.execute(stmt)
            return result.scalars().first()
        except SQLAlchemyError as db_exc:
            logger.error("Database error in get_settings_by_specialization_id", error=str(db_exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(db_exc),
                error_function="get_settings_by_specialization_id",
                error_file="src/repositories/report_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise
        except Exception as exc:
            logger.error("Unexpected error in get_settings_by_specialization_id", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="get_settings_by_specialization_id",
                error_file="src/repositories/report_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def get_last_sent_email_history(self, setting_id: uuid.UUID, email_type: str) -> EmailHistory | None:
        """Fetch the most recent successfully sent email history record.

        Args:
            setting_id: The settings record UUID.
            email_type: The report type ("At-risk" or "Summary report").

        Returns:
            The most recent EmailHistory with status "sent", or None.
        """
        try:
            stmt = (
                select(EmailHistory)
                .where(
                    EmailHistory.setting_id == setting_id,
                    EmailHistory.email_type == email_type,
                    EmailHistory.email_status == "sent",
                    EmailHistory.is_active == 1,
                )
                .order_by(EmailHistory.last_synced.desc())
                .limit(1)
            )
            result = await self._session.execute(stmt)
            return result.scalars().first()
        except SQLAlchemyError as db_exc:
            logger.error("Database error in get_last_sent_email_history", error=str(db_exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(db_exc),
                error_function="get_last_sent_email_history",
                error_file="src/repositories/report_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise
        except Exception as exc:
            logger.error("Unexpected error in get_last_sent_email_history", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="get_last_sent_email_history",
                error_file="src/repositories/report_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def get_email_template_by_name(self, template_name: str) -> EmailTemplate | None:
        """Fetch an email template by its name.

        Args:
            template_name: The template name to look up.

        Returns:
            The EmailTemplate record, or None if not found.
        """
        try:
            stmt = select(EmailTemplate).where(
                EmailTemplate.template_name == template_name,
                EmailTemplate.is_active == 1,
            )
            result = await self._session.execute(stmt)
            return result.scalars().first()
        except SQLAlchemyError as db_exc:
            logger.error("Database error in get_email_template_by_name", error=str(db_exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(db_exc),
                error_function="get_email_template_by_name",
                error_file="src/repositories/report_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise
        except Exception as exc:
            logger.error("Unexpected error in get_email_template_by_name", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="get_email_template_by_name",
                error_file="src/repositories/report_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def get_active_recipients_by_specialization(self, specialization_id: uuid.UUID) -> list[EmailRecipient]:
        """Fetch all active email recipients for a specialization.

        Args:
            specialization_id: The specialization UUID.

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
            logger.error("Database error in get_active_recipients_by_specialization", error=str(db_exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(db_exc),
                error_function="get_active_recipients_by_specialization",
                error_file="src/repositories/report_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise
        except Exception as exc:
            logger.error("Unexpected error in get_active_recipients_by_specialization", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="get_active_recipients_by_specialization",
                error_file="src/repositories/report_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def get_kpi_history_by_specialization(self, specialization_id: uuid.UUID) -> KpiHistory | None:
        """Fetch the most recent KPI history record for a specialization.

        Args:
            specialization_id: The specialization UUID.

        Returns:
            The most recent KpiHistory record, or None.
        """
        try:
            stmt = (
                select(KpiHistory)
                .where(
                    KpiHistory.specialization_id == specialization_id,
                    KpiHistory.is_active == 1,
                )
                .order_by(KpiHistory.created_at.desc())
                .limit(1)
            )
            result = await self._session.execute(stmt)
            return result.scalars().first()
        except SQLAlchemyError as db_exc:
            logger.error("Database error in get_kpi_history_by_specialization", error=str(db_exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(db_exc),
                error_function="get_kpi_history_by_specialization",
                error_file="src/repositories/report_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise
        except Exception as exc:
            logger.error("Unexpected error in get_kpi_history_by_specialization", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="get_kpi_history_by_specialization",
                error_file="src/repositories/report_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def get_at_risk_projects(self, at_risk_threshold: int) -> list[Project]:
        """Fetch projects that are at risk (days since onboarding exceeds threshold).

        Projects are considered at-risk if:
        - They are active (is_active = 1)
        - They have not been completed (completed_at is NULL)
        - Days since onboarded_date exceeds the threshold

        Args:
            at_risk_threshold: Number of days threshold.

        Returns:
            List of at-risk Project records.
        """
        try:
            # Calculate the cutoff date: projects onboarded before this date are at risk
            stmt = select(Project).where(
                Project.is_active == 1,
                Project.completed_at.is_(None),
                func.current_date() - Project.onboarded_date > at_risk_threshold,
            )
            result = await self._session.execute(stmt)
            return list(result.scalars().all())
        except SQLAlchemyError as db_exc:
            logger.error("Database error in get_at_risk_projects", error=str(db_exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(db_exc),
                error_function="get_at_risk_projects",
                error_file="src/repositories/report_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise
        except Exception as exc:
            logger.error("Unexpected error in get_at_risk_projects", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="get_at_risk_projects",
                error_file="src/repositories/report_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def create_email_history(self, email_history: EmailHistory) -> EmailHistory:
        """Insert a new email history record.

        Args:
            email_history: The EmailHistory ORM instance to persist.

        Returns:
            The persisted EmailHistory instance.
        """
        try:
            self._session.add(email_history)
            await self._session.flush()
            return email_history
        except SQLAlchemyError as db_exc:
            logger.error("Database error in create_email_history", error=str(db_exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(db_exc),
                error_function="create_email_history",
                error_file="src/repositories/report_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise
        except Exception as exc:
            logger.error("Unexpected error in create_email_history", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="create_email_history",
                error_file="src/repositories/report_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def create_cron_job(self, cron_job: CronJob) -> CronJob:
        """Insert a new cron job record.

        Args:
            cron_job: The CronJob ORM instance to persist.

        Returns:
            The persisted CronJob instance.
        """
        try:
            self._session.add(cron_job)
            await self._session.flush()
            return cron_job
        except SQLAlchemyError as db_exc:
            logger.error("Database error in create_cron_job", error=str(db_exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(db_exc),
                error_function="create_cron_job",
                error_file="src/repositories/report_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise
        except Exception as exc:
            logger.error("Unexpected error in create_cron_job", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="create_cron_job",
                error_file="src/repositories/report_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def update_cron_job_status(self, cron_id: uuid.UUID, sync_status: str) -> None:
        """Update the sync_status of a cron job record.

        Args:
            cron_id: The cron job UUID.
            sync_status: The new status ("success" or "fail").
        """
        try:
            stmt = (
                update(CronJob)
                .where(CronJob.cron_id == cron_id)
                .values(
                    sync_status=sync_status,
                    modified_at=datetime.utcnow(),
                    modified_by="report_service",
                )
            )
            await self._session.execute(stmt)
            await self._session.flush()
        except SQLAlchemyError as db_exc:
            logger.error("Database error in update_cron_job_status", error=str(db_exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(db_exc),
                error_function="update_cron_job_status",
                error_file="src/repositories/report_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise
        except Exception as exc:
            logger.error("Unexpected error in update_cron_job_status", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="update_cron_job_status",
                error_file="src/repositories/report_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise
