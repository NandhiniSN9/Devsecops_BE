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

    async def get_repository_by_name_and_ticket(
        self, repo_name: str, ticket_id: uuid.UUID
    ) -> Repository | None:
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
