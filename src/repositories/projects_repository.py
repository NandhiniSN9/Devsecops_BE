"""Repository for projects data access operations.

Provides project listing with filtering, sorting, pagination,
and project action operations (mark not applicable, mark complete).
"""

import asyncio
import traceback
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.schema.devsecops_ticket import DevsecopsTicket
from src.repositories.schema.jira_ticket import JiraTicket
from src.repositories.schema.project import Project
from src.repositories.schema.repository import Repository
from src.repositories.schema.status import Status
from src.utils.helpers import log_error_to_db
from src.utils.logger import logger


class ProjectsRepository:
    """Data access layer for projects queries and mutations."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_projects(
        self,
        period_days: int,
        search: str | None,
        status_ids: list[uuid.UUID] | None,
        client_ids: list[str] | None,
        specialization_ids: list[uuid.UUID] | None,
        min_overdue_days: int | None,
        offset: int,
        limit: int,
        sort_by: str,
        sort_order: str,
    ) -> tuple[list[Project], int]:
        """Get paginated projects with filters applied.

        Args:
            period_days: Number of days to look back for onboarded_date filter. 0 means no filter.
            search: Free text search on project name (case-insensitive).
            status_ids: List of status UUIDs to filter by.
            client_ids: List of client identifiers to filter by.
            specialization_ids: List of specialization UUIDs to filter by.
            min_overdue_days: Minimum overdue days — only return projects where overdue >= this value.
            offset: Number of items to skip.
            limit: Number of items per page.
            sort_by: Field to sort by (project_name or onboarded_date).
            sort_order: Sort direction (asc or desc).

        Returns:
            Tuple of (list of Project objects, total count).
        """
        try:
            # Base query: ALL active projects (ServiceNow + DevSecOps)
            base_query = select(Project).join(
                Status, Project.status_id == Status.status_id, isouter=True
            ).where(Project.is_active == 1)

            # Period filter — only apply when period_days > 0
            if period_days > 0:
                cutoff_date = datetime.utcnow().date() - timedelta(days=period_days)
                base_query = base_query.where(Project.onboarded_date >= cutoff_date)

            # Search filter - sanitize search input to prevent SQL injection
            if search:
                # Escape special characters in LIKE pattern
                sanitized_search = search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
                base_query = base_query.where(Project.project_name.ilike(f"%{sanitized_search}%"))

            # Status filter
            if status_ids:
                base_query = base_query.where(Project.status_id.in_(status_ids))

            # Client filter
            if client_ids:
                base_query = base_query.where(Project.client.in_(client_ids))

            # Specialization filter (join through devsecops_tickets)
            if specialization_ids:
                base_query = base_query.where(
                    Project.project_id.in_(
                        select(DevsecopsTicket.project_id)
                        .where(
                            DevsecopsTicket.specialization_id.in_(specialization_ids),
                            DevsecopsTicket.is_active == 1,
                            DevsecopsTicket.project_id.isnot(None),
                        )
                    )
                )

            # Minimum overdue days filter - use ORM expression to prevent SQL injection
            if min_overdue_days is not None and min_overdue_days > 0:
                base_query = base_query.where(
                    func.current_date() - Project.onboarded_date >= min_overdue_days
                )

            # Count total items before pagination
            count_query = select(func.count()).select_from(base_query.subquery())
            count_result = await self._session.execute(count_query)
            total_items = count_result.scalar_one()

            # Sorting
            if sort_by == "onboarded_date":
                order_col = Project.onboarded_date
            else:
                order_col = Project.project_name

            if sort_order == "desc":
                base_query = base_query.order_by(order_col.desc())
            else:
                base_query = base_query.order_by(order_col.asc())

            # Pagination
            base_query = base_query.offset(offset).limit(limit)

            result = await self._session.execute(base_query)
            projects = list(result.scalars().all())

            return projects, total_items

        except Exception as e:
            logger.exception("Failed to fetch projects", extra={"error": str(e)})
            asyncio.create_task(log_error_to_db(
                error_message=str(e),
                error_function="get_projects",
                error_file="src/repositories/projects_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def get_repositories_for_project(self, project_id: uuid.UUID) -> list[Repository]:
        """Get repositories linked to a project through devsecops_tickets.

        Args:
            project_id: The project UUID.

        Returns:
            List of Repository objects linked to the project.
        """
        try:       
            stmt = (
                select(Repository)
                .join(DevsecopsTicket, Repository.ticket_id == DevsecopsTicket.ticket_id)
                .where(
                    DevsecopsTicket.project_id == project_id,
                    DevsecopsTicket.is_active == 1,
                    Repository.is_active == 1,
                )
            )
            result = await self._session.execute(stmt)
            return list(result.scalars().all())

        except Exception as e:
            logger.exception(
                "Failed to fetch repositories for project",
                extra={"project_id": str(project_id), "error": str(e)},
            )
            asyncio.create_task(log_error_to_db(
                error_message=str(e),
                error_function="get_repositories_for_project",
                error_file="src/repositories/projects_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise


    async def get_project_by_id(self, project_id: uuid.UUID) -> Project | None:
        """Get a single active project by ID.

        Args:
            project_id: The project UUID.

        Returns:
            Project object or None if not found.
        """
        try:             
            stmt = select(Project).where(
                Project.project_id == project_id,
                Project.is_active == 1,
            )
            result = await self._session.execute(stmt)
            return result.scalar_one_or_none()

        except Exception as e:
            logger.exception(
                "Failed to fetch project by id",
                extra={"project_id": str(project_id), "error": str(e)},
            )
            asyncio.create_task(log_error_to_db(
                error_message=str(e),
                error_function="get_project_by_id",
                error_file="src/repositories/projects_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def get_status_by_name(self, status_name: str) -> Status | None:
        """Look up a status by name.

        Args:
            status_name: The status name to look up.

        Returns:
            Status object or None if not found.
        """
        try:              
            stmt = select(Status).where(
                Status.status_name == status_name,
                Status.is_active == 1,
            )
            result = await self._session.execute(stmt)
            return result.scalar_one_or_none()

        except Exception as e:
            logger.exception(
                "Failed to fetch status by name",
                extra={"status_name": status_name, "error": str(e)},
            )
            asyncio.create_task(log_error_to_db(
                error_message=str(e),
                error_function="get_status_by_name",
                error_file="src/repositories/projects_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def update_project_not_applicable(
        self,
        project_id: uuid.UUID,
        status_id: uuid.UUID,
        modified_by: str,
    ) -> None:
        """Update project to Not Applicable status (sets is_applicable = False).

        Args:
            project_id: The project UUID.
            status_id: The Not Applicable status UUID.
            modified_by: The user performing the action.
        """
        try:
            stmt = (
                update(Project)
                .where(Project.project_id == project_id)
                .values(
                    is_applicable=False,
                    status_id=status_id,
                    modified_at=func.current_timestamp(),
                    modified_by=modified_by,
                )
            )
            await self._session.execute(stmt)

        except Exception as exc:
            logger.exception(
                "Failed to update project to not-applicable",
                extra={"project_id": str(project_id)},
            )
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="update_project_not_applicable",
                error_file="src/repositories/projects_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise


    async def update_project_complete(
        self,
        project_id: uuid.UUID,
        status_id: uuid.UUID,
        modified_by: str,
    ) -> None:
        """Update project to Completed status and stamp completed_at on devsecops_tickets.

        Sets ``completed_at`` (timezone-aware UTC) on every active
        ``devsecops_tickets`` row linked to the project.

        Args:
            project_id: The project UUID.
            status_id: The Completed status UUID.
            modified_by: The user performing the action.
        """
        try:
            now_utc = datetime.now(timezone.utc)
            now_naive = now_utc.replace(tzinfo=None)

            # Update projects table — status and modified fields only (completed_at lives on tickets)
            stmt = (
                update(Project)
                .where(Project.project_id == project_id)
                .values(
                    status_id=status_id,
                    modified_at=now_naive,
                    modified_by=modified_by,
                    
                )
            )
            await self._session.execute(stmt)

            # Stamp completed_at on all linked devsecops_tickets rows (TIMESTAMPTZ — timezone-aware)
            ticket_stmt = (
                update(DevsecopsTicket)
                .where(
                    DevsecopsTicket.project_id == project_id,
                    DevsecopsTicket.is_active == 1,
                )
                .values(
                    completed_at=now_utc,
                    modified_at=now_naive,
                    modified_by=modified_by,
                )
            )
            await self._session.execute(ticket_stmt)

        except Exception as exc:
            logger.exception(
                "Failed to update project to complete",
                extra={"project_id": str(project_id)},
            )
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="update_project_complete",
                error_file="src/repositories/projects_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise


    async def create_jira_ticket(
        self,
        project_id: uuid.UUID,
        jira_id: str,
        reason_category: str,
        comments: str,
        evidence_url: str | None,
        created_by: str,
    ) -> None:
        """Create a local jira_tickets record after the Jira bug has been created.

        Args:
            project_id: The project UUID.
            jira_id: The Jira issue key returned by the Jira API (e.g. SBT-42).
            reason_category: Reason category for not applicable.
            comments: Detailed comments.
            evidence_url: URL of uploaded evidence file or None.
            created_by: The user performing the action.
        """
        try:
            jira_ticket = JiraTicket(
                project_id=project_id,
                jira_id=jira_id,
                type="Not Applicable",
                assignee=created_by,
                priority="Medium",
                status="Open",
                reason_category=reason_category,
                comments=comments,
                evidence_url=evidence_url,
            )
            jira_ticket.created_by = created_by
            self._session.add(jira_ticket)

        except Exception as exc:
            logger.exception(
                "Failed to create local jira_ticket record",
                extra={"project_id": str(project_id), "jira_id": jira_id},
            )
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="create_jira_ticket",
                error_file="src/repositories/projects_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def commit(self) -> None:
        """Commit the current transaction."""
        try:
            await self._session.commit()
        except Exception as e:
            logger.exception("Failed to commit transaction", extra={"error": str(e)})
            asyncio.create_task(log_error_to_db(
                error_message=str(e),
                error_function="commit",
                error_file="src/repositories/projects_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def rollback(self) -> None:
        """Rollback the current transaction."""
        try:        
            await self._session.rollback()

        except Exception as e:
            logger.exception("Failed to rollback transaction", extra={"error": str(e)})
            asyncio.create_task(log_error_to_db(
                error_message=str(e),
                error_function="rollback",
                error_file="src/repositories/projects_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def get_status_name_for_project(self, project: Project) -> str | None:
        """Get the status name for a project.

        For devsecops-onboarded projects, first check the linked devsecops_ticket.status_id.
        Falls back to project.status_id if no ticket status is found.

        Args:
            project: The project object.

        Returns:
            Status name string or None.
        """

        try:
            # For devsecops-onboarded projects, try to get status from linked ticket first
            if project.is_devsecops_onboarded:
                ticket_status_stmt = (
                    select(Status.status_name)
                    .join(DevsecopsTicket, DevsecopsTicket.status_id == Status.status_id)
                    .where(
                        DevsecopsTicket.project_id == project.project_id,
                        DevsecopsTicket.is_active == 1,
                        DevsecopsTicket.status_id.isnot(None),
                    )
                    .limit(1)
                )
                ticket_result = await self._session.execute(ticket_status_stmt)
                ticket_status_name = ticket_result.scalar_one_or_none()
                if ticket_status_name:
                    return ticket_status_name

            # Fall back to project.status_id
            if project.status_id is None:
                return None
            stmt = select(Status.status_name).where(Status.status_id == project.status_id)
            result = await self._session.execute(stmt)
            return result.scalar_one_or_none()

        except Exception as e:
            logger.exception(
                "Failed to fetch status name for project",
                extra={"project_id": str(project.project_id), "error": str(e)},
            )
            asyncio.create_task(log_error_to_db(
                error_message=str(e),
                error_function="get_status_name_for_project",
                error_file="src/repositories/projects_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def get_not_applicable_details(self, project_id: uuid.UUID) -> dict | None:
        """Get jira ticket details for a Not Applicable project.

        Args:
            project_id: The project UUID.

        Returns:
            Dictionary with jira ticket details or None if not found.
        """
        try:
            stmt = select(JiraTicket).where(
                JiraTicket.project_id == project_id,
                JiraTicket.is_active == 1,
            )
            result = await self._session.execute(stmt)
            jira_ticket = result.scalar_one_or_none()
            if not jira_ticket:
                return None
            return {
                "reason_category": jira_ticket.reason_category,
                "comments": jira_ticket.comments,
                "evidence_url": jira_ticket.evidence_url,
                "type": jira_ticket.type,
                "priority": jira_ticket.priority,
                "assignee": jira_ticket.assignee,
                "jira_status": jira_ticket.status,
            }

        except Exception as e:
            logger.exception(
                "Failed to fetch not_applicable_details",
                extra={"project_id": str(project_id), "error": str(e)},
            )
            asyncio.create_task(log_error_to_db(
                error_message=str(e),
                error_function="get_not_applicable_details",
                error_file="src/repositories/projects_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise
