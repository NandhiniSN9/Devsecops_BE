"""Repository for ServiceNow sync data access operations.

Provides project lookup/creation, ticket insertion, repository insertion,
and reference data resolution for the ServiceNow integration endpoints.
"""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.schema.devsecops_ticket import DevsecopsTicket
from src.repositories.schema.project import Project
from src.repositories.schema.repository import Repository
from src.repositories.schema.specialization import Specialization
from src.repositories.schema.status import Status


class ServiceNowRepository:
    """Data access layer for ServiceNow sync operations."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_project_by_sn_project_id(self, sn_project_id: str) -> Project | None:
        """Look up an active project by its ServiceNow project identifier.

        Args:
            sn_project_id: The ServiceNow project ID to search for.

        Returns:
            The matching Project record, or None if not found.
        """
        stmt = select(Project).where(
            Project.sn_project_id == sn_project_id,
            Project.is_active == 1,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_project_by_name(self, project_name: str) -> Project | None:
        """Look up an active project by project name.

        Args:
            project_name: The project name to search for.

        Returns:
            The first matching Project record, or None if not found.
        """
        stmt = select(Project).where(
            func.lower(Project.project_name) == func.lower(project_name),
            Project.is_active == 1,
        )
        result = await self._session.execute(stmt)
        return result.scalars().first()

    async def get_project_by_client(self, client: str) -> Project | None:
        """Look up an active project by client name.

        Args:
            client: The client name to search for.

        Returns:
            The first matching Project record, or None if not found.
        """
        stmt = select(Project).where(
            func.lower(Project.client) == func.lower(client),
            Project.is_active == 1,
        )
        result = await self._session.execute(stmt)
        return result.scalars().first()

    async def get_default_project(self) -> Project | None:
        """Get the default project record from the database.

        The default project is identified by project_name = 'Default'.

        Returns:
            The default Project record, or None if not found.
        """
        stmt = select(Project).where(
            func.lower(Project.project_name) == "default",
            Project.is_active == 1,
        )
        result = await self._session.execute(stmt)
        return result.scalars().first()

    async def get_inactive_status(self) -> Status | None:
        """Get the 'Inactive' status record from the statuses table.

        Returns:
            The Inactive Status record, or None if not found.
        """
        stmt = select(Status).where(
            func.lower(Status.status_name) == "inactive",
            Status.is_active == 1,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_specialization_by_name(self, specialization_name: str) -> Specialization | None:
        """Look up an active specialization by name (case-insensitive).

        Args:
            specialization_name: The specialization name to search for.

        Returns:
            The matching Specialization record, or None if not found.
        """
        stmt = select(Specialization).where(
            func.lower(Specialization.specialization_name) == func.lower(specialization_name),
            Specialization.is_active == 1,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_project(self, project: Project) -> Project:
        """Insert a new project record into the database.

        Args:
            project: The Project ORM instance to persist.

        Returns:
            The persisted Project instance.
        """
        self._session.add(project)
        await self._session.flush()
        return project

    async def update_project(
        self,
        project: Project,
        project_name: str,
        onboarded_date,
        project_type: str,
        specialization_name: str | None,
        is_applicable: bool,
        client: str | None,
        modified_by: str,
    ) -> Project:
        """Update an existing project record with new details.

        Args:
            project: The existing Project ORM instance to update.
            project_name: Updated project name.
            onboarded_date: Updated onboarded date.
            project_type: Updated project type.
            specialization_name: Updated specialization name.
            is_applicable: Updated applicability flag.
            client: Updated client name.
            modified_by: The service account performing the update.

        Returns:
            The updated Project instance.
        """
        from datetime import datetime

        project.project_name = project_name
        project.onboarded_date = onboarded_date
        project.project_type = project_type
        project.specialization_name = specialization_name
        project.is_applicable = is_applicable
        project.client = client
        project.modified_at = datetime.utcnow()
        project.modified_by = modified_by
        await self._session.flush()
        return project

    async def create_ticket(self, ticket: DevsecopsTicket) -> DevsecopsTicket:
        """Insert a new DevSecOps ticket record into the database.

        Args:
            ticket: The DevsecopsTicket ORM instance to persist.

        Returns:
            The persisted DevsecopsTicket instance.
        """
        self._session.add(ticket)
        await self._session.flush()
        return ticket

    async def get_ticket_by_sn_or_devsec_id(
        self, sn_project_id: str, devsec_project_id: str | None
    ) -> DevsecopsTicket | None:
        """Look up an existing ticket by sn_project_id or devSec_project_id.

        Checks sn_project_id first, then devSec_project_id as fallback.

        Args:
            sn_project_id: The ServiceNow project ID.
            devsec_project_id: The Azure DevOps project ID (optional).

        Returns:
            The matching DevsecopsTicket record, or None if not found.
        """
        from sqlalchemy import or_

        conditions = [DevsecopsTicket.sn_project_id == sn_project_id]
        if devsec_project_id:
            conditions.append(DevsecopsTicket.devsec_project_id == devsec_project_id)

        stmt = select(DevsecopsTicket).where(
            or_(*conditions),
            DevsecopsTicket.is_active == 1,
        )
        result = await self._session.execute(stmt)
        return result.scalars().first()

    async def update_ticket(
        self,
        ticket: DevsecopsTicket,
        specialization_id: uuid.UUID,
        project_id: uuid.UUID,
        sn_project_id: str | None,
        devsec_project_id: str | None,
        project_name: str,
        client: str | None,
        requested_by: str | None,
        approver: str | None,
        requested_at=None,
        modified_by: str = "",
    ) -> DevsecopsTicket:
        """Update an existing ticket record with new details.

        Args:
            ticket: The existing DevsecopsTicket ORM instance.
            specialization_id: Updated specialization ID.
            project_id: Updated project ID.
            sn_project_id: Updated ServiceNow project ID.
            devsec_project_id: Updated DevSec project ID.
            project_name: Updated project name.
            client: Updated client.
            requested_by: Updated requester.
            approver: Updated approver.
            requested_at: Updated request timestamp.
            modified_by: The service account performing the update.

        Returns:
            The updated DevsecopsTicket instance.
        """
        from datetime import datetime

        ticket.specialization_id = specialization_id
        ticket.project_id = project_id
        ticket.sn_project_id = sn_project_id
        ticket.devsec_project_id = devsec_project_id
        ticket.project_name = project_name
        ticket.client = client
        ticket.requested_by = requested_by
        ticket.approver = approver
        ticket.requested_at = requested_at.replace(tzinfo=None) if requested_at else None
        ticket.modified_at = datetime.utcnow()
        ticket.modified_by = modified_by
        await self._session.flush()
        return ticket

    async def get_repository_by_name_and_ticket(self, repo_name: str, ticket_id: uuid.UUID) -> Repository | None:
        """Look up a repository by name and ticket ID.

        Args:
            repo_name: The repository name.
            ticket_id: The ticket UUID the repository belongs to.

        Returns:
            The matching Repository record, or None if not found.
        """
        stmt = select(Repository).where(
            Repository.repository_name == repo_name,
            Repository.ticket_id == ticket_id,
            Repository.is_active == 1,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_repository_by_ado_repo_id_and_ticket(
        self, ado_repo_id: str, ticket_id: uuid.UUID
    ) -> Repository | None:
        """Look up a repository by ado_repo_id and ticket ID.

        Args:
            ado_repo_id: The Azure DevOps repository identifier.
            ticket_id: The ticket UUID the repository belongs to.

        Returns:
            The matching Repository record, or None if not found.
        """
        stmt = select(Repository).where(
            Repository.ado_repo_id == ado_repo_id,
            Repository.ticket_id == ticket_id,
            Repository.is_active == 1,
        )
        result = await self._session.execute(stmt)
        return result.scalars().first()

    async def update_repository(
        self,
        repository: Repository,
        repository_name: str,
        lead_approvers: str | None,
        modified_by: str,
    ) -> Repository:
        """Update an existing repository record.

        Args:
            repository: The existing Repository ORM instance.
            repository_name: Updated repository name.
            lead_approvers: Updated lead approvers (comma-separated).
            modified_by: The service account performing the update.

        Returns:
            The updated Repository instance.
        """
        from datetime import datetime

        repository.repository_name = repository_name
        repository.lead_approvers = lead_approvers
        repository.modified_at = datetime.utcnow()
        repository.modified_by = modified_by
        await self._session.flush()
        return repository

    async def create_repository(self, repository: Repository) -> Repository:
        """Insert a new repository record into the database.

        Args:
            repository: The Repository ORM instance to persist.

        Returns:
            The persisted Repository instance.
        """
        self._session.add(repository)
        await self._session.flush()
        return repository

    async def commit(self) -> None:
        """Commit the current transaction."""
        await self._session.commit()
