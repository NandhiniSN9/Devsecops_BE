"""Repository for projects data access operations.

Provides project listing with filtering, sorting, pagination,
and project action operations (mark not applicable, mark complete).
"""

import uuid
from datetime import datetime, timedelta

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.schema.devsecops_ticket import DevsecopsTicket
from src.repositories.schema.jira_ticket import JiraTicket
from src.repositories.schema.project import Project
from src.repositories.schema.repository import Repository
from src.repositories.schema.status import Status


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
        offset: int,
        limit: int,
        sort_by: str,
        sort_order: str,
    ) -> tuple[list[Project], int]:
        """Get paginated projects with filters applied.

        Args:
            period_days: Number of days to look back for onboarded_date filter.
            search: Free text search on project name (case-insensitive).
            status_ids: List of status UUIDs to filter by.
            client_ids: List of client identifiers to filter by.
            specialization_ids: List of specialization UUIDs to filter by.
            offset: Number of items to skip.
            limit: Number of items per page.
            sort_by: Field to sort by (project_name or onboarded_date).
            sort_order: Sort direction (asc or desc).

        Returns:
            Tuple of (list of Project objects, total count).
        """
        # Base query: active projects only
        base_query = select(Project).join(
            Status, Project.status_id == Status.status_id, isouter=True
        ).where(Project.is_active == 1)

        # Period filter
        cutoff_date = datetime.utcnow().date() - timedelta(days=period_days)
        base_query = base_query.where(Project.onboarded_date >= cutoff_date)

        # Search filter
        if search:
            base_query = base_query.where(Project.project_name.ilike(f"%{search}%"))

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

    async def get_repositories_for_project(self, project_id: uuid.UUID) -> list[Repository]:
        """Get repositories linked to a project through devsecops_tickets.

        Args:
            project_id: The project UUID.

        Returns:
            List of Repository objects linked to the project.
        """
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

    async def get_project_by_id(self, project_id: uuid.UUID) -> Project | None:
        """Get a single active project by ID.

        Args:
            project_id: The project UUID.

        Returns:
            Project object or None if not found.
        """
        stmt = select(Project).where(
            Project.project_id == project_id,
            Project.is_active == 1,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_status_by_name(self, status_name: str) -> Status | None:
        """Look up a status by name.

        Args:
            status_name: The status name to look up.

        Returns:
            Status object or None if not found.
        """
        stmt = select(Status).where(
            Status.status_name == status_name,
            Status.is_active == 1,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_project_not_applicable(
        self,
        project_id: uuid.UUID,
        status_id: uuid.UUID,
        modified_by: str,
    ) -> None:
        """Update project to Not Applicable status.

        Args:
            project_id: The project UUID.
            status_id: The Not Applicable status UUID.
            modified_by: The user performing the action.
        """
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

    async def update_project_complete(
        self,
        project_id: uuid.UUID,
        status_id: uuid.UUID,
        modified_by: str,
    ) -> None:
        """Update project to Completed status.

        Args:
            project_id: The project UUID.
            status_id: The Completed status UUID.
            modified_by: The user performing the action.
        """
        stmt = (
            update(Project)
            .where(Project.project_id == project_id)
            .values(
                status_id=status_id,
                completed_at=func.current_timestamp(),
                modified_at=func.current_timestamp(),
                modified_by=modified_by,
            )
        )
        await self._session.execute(stmt)

    async def create_jira_ticket(
        self,
        project_id: uuid.UUID,
        jira_id: str,
        reason_category: str,
        comments: str,
        evidence_url: str | None,
        created_by: str,
    ) -> None:
        """Create a Jira ticket record for Not Applicable action.

        Args:
            project_id: The project UUID.
            jira_id: Generated Jira identifier.
            reason_category: Reason category for not applicable.
            comments: Detailed comments.
            evidence_url: URL of uploaded evidence file or None.
            created_by: The user performing the action.
        """
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

    async def commit(self) -> None:
        """Commit the current transaction."""
        await self._session.commit()

    async def rollback(self) -> None:
        """Rollback the current transaction."""
        await self._session.rollback()

    async def get_status_name_for_project(self, project: Project) -> str | None:
        """Get the status name for a project.

        Args:
            project: The project object.

        Returns:
            Status name string or None.
        """
        if project.status_id is None:
            return None
        stmt = select(Status.status_name).where(Status.status_id == project.status_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
