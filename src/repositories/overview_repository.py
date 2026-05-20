"""Repository for overview dashboard data access operations.

Computes KPI counts live from the projects table and retrieves
historical snapshots from kpi_history for trend calculation.
"""

import asyncio
import traceback
import uuid
from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.schema.cron_job import CronJob
from src.repositories.schema.kpi_history import KpiHistory
from src.repositories.schema.project import Project
from src.repositories.schema.setting import Setting
from src.repositories.schema.specialization import Specialization
from src.repositories.schema.status import Status
from src.utils.logger import logger


class OverviewRepository:
    """Data access layer for overview dashboard queries."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_live_counts(self, specialization_ids: list | None = None) -> dict:
        """Get current project counts directly from the projects table.

        Computes:
        - total_projects: all active projects (optionally filtered by specialization)
        - adopted: projects with is_devsecops_onboarded = true
        - completed/active/inactive/at_risk/not_applicable: by status name

        Args:
            specialization_ids: Optional list of specialization UUIDs to filter by.

        Returns:
            Dict with count keys: total_projects, adopted, completed, active,
            inactive, at_risk, not_applicable.
        """
        try:
            # Base filter conditions
            base_conditions = [Project.is_active == 1]
            if specialization_ids:
                base_conditions.append(Project.specialization_name.in_(
                    select(Specialization.specialization_name)
                    .where(Specialization.specialization_id.in_(specialization_ids))
                    .scalar_subquery()
                ))

            # Total active projects
            total_stmt = select(func.count()).select_from(Project).where(*base_conditions)
            total_result = await self._session.execute(total_stmt)
            total_projects = total_result.scalar_one()

            # Adopted (is_devsecops_onboarded = true)
            adopted_stmt = select(func.count()).select_from(Project).where(
                *base_conditions,
                Project.is_devsecops_onboarded.is_(True),
            )
            adopted_result = await self._session.execute(adopted_stmt)
            adopted = adopted_result.scalar_one()

            # Counts by status name
            status_counts_stmt = (
                select(Status.status_name, func.count(Project.project_id))
                .join(Project, Project.status_id == Status.status_id)
                .where(*base_conditions, Status.is_active == 1)
                .group_by(Status.status_name)
            )
            status_result = await self._session.execute(status_counts_stmt)
            status_rows = status_result.all()

            # Build status map
            status_map = {row[0]: row[1] for row in status_rows}

            return {
                "total_projects": total_projects,
                "adopted": adopted,
                "completed": status_map.get("Completed", 0),
                "active": status_map.get("Active", 0),
                "inactive": status_map.get("Inactive", 0),
                "at_risk": status_map.get("At Risk", 0),
                "not_applicable": status_map.get("Not Applicable", 0),
            }

        except SQLAlchemyError as db_exc:
            logger.error("Database error in get_live_counts", error=str(db_exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(db_exc),
                error_function="get_live_counts",
                error_file="src/repositories/overview_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise
        except Exception as exc:
            logger.error("Unexpected error in get_live_counts", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="get_live_counts",
                error_file="src/repositories/overview_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def get_historical_counts(self, days_ago: int) -> dict | None:
        """Get project counts from kpi_history for a specific date in the past.

        Sums counts across all specializations for the target date.
        Falls back to the closest record before the target date.

        Args:
            days_ago: Number of days to look back (7, 30, or 90).

        Returns:
            Dict with count keys matching get_live_counts, or None if no history.
        """
        try:
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            target_date = today_start - timedelta(days=days_ago)

            # Get the most recent kpi_history records on or before target date
            # (one per specialization, pick the latest)
            row_number = (
                func.row_number()
                .over(
                    partition_by=KpiHistory.specialization_id,
                    order_by=KpiHistory.created_at.desc(),
                )
                .label("rn")
            )

            subquery = (
                select(KpiHistory, row_number)
                .where(
                    KpiHistory.created_at <= target_date + timedelta(days=1),
                    KpiHistory.is_active == 1,
                )
                .subquery()
            )

            stmt = select(
                func.sum(subquery.c.projects_count),
                func.sum(subquery.c.completed_count),
                func.sum(subquery.c.active_count),
                func.sum(subquery.c.inactive_count),
                func.sum(subquery.c.at_risk_count),
                func.sum(subquery.c.not_applicable_count),
            ).where(subquery.c.rn == 1)

            result = await self._session.execute(stmt)
            row = result.one_or_none()

            if not row or row[0] is None:
                return None

            # Note: kpi_history doesn't have adopted_count yet,
            # so we estimate it as 0 for historical comparison
            return {
                "total_projects": row[0] or 0,
                "adopted": 0,  # Historical adopted not tracked in kpi_history
                "completed": row[1] or 0,
                "active": row[2] or 0,
                "inactive": row[3] or 0,
                "at_risk": row[4] or 0,
                "not_applicable": row[5] or 0,
            }

        except SQLAlchemyError as db_exc:
            logger.error("Database error in get_historical_counts", error=str(db_exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(db_exc),
                error_function="get_historical_counts",
                error_file="src/repositories/overview_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise
        except Exception as exc:
            logger.error("Unexpected error in get_historical_counts", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="get_historical_counts",
                error_file="src/repositories/overview_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def get_last_synced(self) -> datetime | None:
        """Get the most recent last_synced timestamp from the settings table.

        Returns:
            The most recent last_synced datetime, or None if no records found.
        """
        try:
            stmt = select(func.max(Setting.last_synced)).where(Setting.is_active == 1)
            result = await self._session.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as db_exc:
            logger.error("Database error in get_last_synced", error=str(db_exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(db_exc),
                error_function="get_last_synced",
                error_file="src/repositories/overview_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise
        except Exception as exc:
            logger.error("Unexpected error in get_last_synced", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="get_last_synced",
                error_file="src/repositories/overview_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def is_sync_in_progress(self) -> bool:
        """Check if any ADO sync operation is currently in progress.

        Returns:
            True if a sync is in progress, False otherwise.
        """
        try:
            stmt = select(func.count()).select_from(CronJob).where(
                CronJob.type == "azure",
                CronJob.sync_status == "pending",
                CronJob.is_active == 1,
            )
            result = await self._session.execute(stmt)
            count = result.scalar_one()
            return count > 0
        except SQLAlchemyError as db_exc:
            logger.error("Database error in is_sync_in_progress", error=str(db_exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(db_exc),
                error_function="is_sync_in_progress",
                error_file="src/repositories/overview_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise
        except Exception as exc:
            logger.error("Unexpected error in is_sync_in_progress", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="is_sync_in_progress",
                error_file="src/repositories/overview_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise
