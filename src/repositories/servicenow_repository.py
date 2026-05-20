"""Repository for ServiceNow sync data access operations.

Provides project lookup/creation, ticket insertion, repository insertion,
and reference data resolution for the ServiceNow integration endpoints.
"""

import asyncio
import traceback
import uuid
from datetime import datetime
from sqlalchemy import func, or_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from src.repositories.schema.devsecops_ticket import DevsecopsTicket
from src.repositories.schema.project import Project
from src.repositories.schema.repository import Repository
from src.repositories.schema.specialization import Specialization
from src.repositories.schema.status import Status
from src.utils.logger import logger
from src.utils.text import normalize_project_name


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
        try:
            stmt = select(Project).where(
                Project.sn_project_id == sn_project_id,
                Project.is_active == 1,
            )
            result = await self._session.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as db_exc:
            logger.error("Database error in get_project_by_sn_project_id", error=str(db_exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(db_exc),
                error_function="get_project_by_sn_project_id",
                error_file="src/repositories/servicenow_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise
        except Exception as exc:
            logger.error("Unexpected error in get_project_by_sn_project_id", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="get_project_by_sn_project_id",
                error_file="src/repositories/servicenow_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def get_project_by_name(self, project_name: str) -> Project | None:
        """Look up an active project by project name.

        Args:
            project_name: The project name to search for.

        Returns:
            The first matching Project record, or None if not found.
        """
        try:
            stmt = select(Project).where(
                func.lower(Project.project_name) == func.lower(project_name),
                Project.is_active == 1,
            )
            result = await self._session.execute(stmt)
            return result.scalars().first()
        except SQLAlchemyError as db_exc:
            logger.error("Database error in get_project_by_name", error=str(db_exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(db_exc),
                error_function="get_project_by_name",
                error_file="src/repositories/servicenow_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise
        except Exception as exc:
            logger.error("Unexpected error in get_project_by_name", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="get_project_by_name",
                error_file="src/repositories/servicenow_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def get_project_by_client(self, client: str) -> Project | None:
        """Look up an active project by client name.

        Args:
            client: The client name to search for.

        Returns:
            The first matching Project record, or None if not found.
        """
        try:
            stmt = select(Project).where(
                func.lower(Project.client) == func.lower(client),
                Project.is_active == 1,
            )
            result = await self._session.execute(stmt)
            return result.scalars().first()
        except SQLAlchemyError as db_exc:
            logger.error("Database error in get_project_by_client", error=str(db_exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(db_exc),
                error_function="get_project_by_client",
                error_file="src/repositories/servicenow_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise
        except Exception as exc:
            logger.error("Unexpected error in get_project_by_client", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="get_project_by_client",
                error_file="src/repositories/servicenow_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def get_project_by_normalized_name(self, ticket_project_name: str) -> Project | None:
        """Look up an active project by normalized name comparison.

        Normalization: remove 'zeb-' prefix, replace '-' with space, lowercase, trim.

        Args:
            ticket_project_name: The ticket's project name to normalize and match.

        Returns:
            The first matching Project record, or None if not found.
        """
        try:
            normalized_ticket_name = normalize_project_name(ticket_project_name)
            if not normalized_ticket_name:
                return None

            stmt = select(Project).where(Project.is_active == 1)
            result = await self._session.execute(stmt)
            projects = result.scalars().all()

            for project in projects:
                if normalize_project_name(project.project_name) == normalized_ticket_name:
                    return project

            return None
        except SQLAlchemyError as db_exc:
            logger.error("Database error in get_project_by_normalized_name", error=str(db_exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(db_exc),
                error_function="get_project_by_normalized_name",
                error_file="src/repositories/servicenow_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise
        except Exception as exc:
            logger.error("Unexpected error in get_project_by_normalized_name", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="get_project_by_normalized_name",
                error_file="src/repositories/servicenow_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def get_default_project(self) -> Project | None:
        """Get the default project record from the database.

        The default project is identified by project_name = 'Default'.

        Returns:
            The default Project record, or None if not found.
        """
        try:
            stmt = select(Project).where(
                func.lower(Project.project_name) == "default",
                Project.is_active == 1,
            )
            result = await self._session.execute(stmt)
            return result.scalars().first()
        except SQLAlchemyError as db_exc:
            logger.error("Database error in get_default_project", error=str(db_exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(db_exc),
                error_function="get_default_project",
                error_file="src/repositories/servicenow_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise
        except Exception as exc:
            logger.error("Unexpected error in get_default_project", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="get_default_project",
                error_file="src/repositories/servicenow_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def get_inactive_status(self) -> Status | None:
        """Get the 'Inactive' status record from the statuses table.

        Returns:
            The Inactive Status record, or None if not found.
        """
        try:
            stmt = select(Status).where(
                func.lower(Status.status_name) == "inactive",
                Status.is_active == 1,
            )
            result = await self._session.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as db_exc:
            logger.error("Database error in get_inactive_status", error=str(db_exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(db_exc),
                error_function="get_inactive_status",
                error_file="src/repositories/servicenow_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise
        except Exception as exc:
            logger.error("Unexpected error in get_inactive_status", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="get_inactive_status",
                error_file="src/repositories/servicenow_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def get_specialization_by_name(self, specialization_name: str) -> Specialization | None:
        """Look up an active specialization by name (case-insensitive).

        Args:
            specialization_name: The specialization name to search for.

        Returns:
            The matching Specialization record, or None if not found.
        """
        try:
            stmt = select(Specialization).where(
                func.lower(Specialization.specialization_name) == func.lower(specialization_name),
                Specialization.is_active == 1,
            )
            result = await self._session.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as db_exc:
            logger.error("Database error in get_specialization_by_name", error=str(db_exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(db_exc),
                error_function="get_specialization_by_name",
                error_file="src/repositories/servicenow_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise
        except Exception as exc:
            logger.error("Unexpected error in get_specialization_by_name", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="get_specialization_by_name",
                error_file="src/repositories/servicenow_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def create_project(self, project: Project) -> Project:
        """Insert a new project record into the database.

        Args:
            project: The Project ORM instance to persist.

        Returns:
            The persisted Project instance.
        """
        try:
            self._session.add(project)
            await self._session.flush()
            return project
        except SQLAlchemyError as db_exc:
            logger.error("Database error in create_project", error=str(db_exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(db_exc),
                error_function="create_project",
                error_file="src/repositories/servicenow_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise
        except Exception as exc:
            logger.error("Unexpected error in create_project", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="create_project",
                error_file="src/repositories/servicenow_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

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
        """Update an existing project record with new details."""
        try:
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
        except SQLAlchemyError as db_exc:
            logger.error("Database error in update_project", error=str(db_exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(db_exc),
                error_function="update_project",
                error_file="src/repositories/servicenow_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise
        except Exception as exc:
            logger.error("Unexpected error in update_project", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="update_project",
                error_file="src/repositories/servicenow_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def create_ticket(self, ticket: DevsecopsTicket) -> DevsecopsTicket:
        """Insert a new DevSecOps ticket record into the database.

        Args:
            ticket: The DevsecopsTicket ORM instance to persist.

        Returns:
            The persisted DevsecopsTicket instance.
        """
        try:
            self._session.add(ticket)
            await self._session.flush()
            return ticket
        except SQLAlchemyError as db_exc:
            logger.error("Database error in create_ticket", error=str(db_exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(db_exc),
                error_function="create_ticket",
                error_file="src/repositories/servicenow_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise
        except Exception as exc:
            logger.error("Unexpected error in create_ticket", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="create_ticket",
                error_file="src/repositories/servicenow_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def get_ticket_by_sn_or_devsec_id(
        self, sn_project_id: str, devsec_project_id: str | None
    ) -> DevsecopsTicket | None:
        """Look up an existing ticket by sn_project_id or devSec_project_id."""
        try:
            conditions = [DevsecopsTicket.sn_project_id == sn_project_id]
            if devsec_project_id:
                conditions.append(DevsecopsTicket.devsec_project_id == devsec_project_id)

            stmt = select(DevsecopsTicket).where(
                or_(*conditions),
                DevsecopsTicket.is_active == 1,
            )
            result = await self._session.execute(stmt)
            return result.scalars().first()
        except SQLAlchemyError as db_exc:
            logger.error("Database error in get_ticket_by_sn_or_devsec_id", error=str(db_exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(db_exc),
                error_function="get_ticket_by_sn_or_devsec_id",
                error_file="src/repositories/servicenow_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise
        except Exception as exc:
            logger.error("Unexpected error in get_ticket_by_sn_or_devsec_id", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="get_ticket_by_sn_or_devsec_id",
                error_file="src/repositories/servicenow_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

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
        """Update an existing ticket record with new details."""
        try:
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
        except SQLAlchemyError as db_exc:
            logger.error("Database error in update_ticket", error=str(db_exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(db_exc),
                error_function="update_ticket",
                error_file="src/repositories/servicenow_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise
        except Exception as exc:
            logger.error("Unexpected error in update_ticket", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="update_ticket",
                error_file="src/repositories/servicenow_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def get_repository_by_name_and_ticket(self, repo_name: str, ticket_id: uuid.UUID) -> Repository | None:
        """Look up a repository by name and ticket ID.

        Args:
            repo_name: The repository name.
            ticket_id: The ticket UUID the repository belongs to.

        Returns:
            The matching Repository record, or None if not found.
        """
        try:
            stmt = select(Repository).where(
                Repository.repository_name == repo_name,
                Repository.ticket_id == ticket_id,
                Repository.is_active == 1,
            )
            result = await self._session.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as db_exc:
            logger.error("Database error in get_repository_by_name_and_ticket", error=str(db_exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(db_exc),
                error_function="get_repository_by_name_and_ticket",
                error_file="src/repositories/servicenow_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise
        except Exception as exc:
            logger.error("Unexpected error in get_repository_by_name_and_ticket", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="get_repository_by_name_and_ticket",
                error_file="src/repositories/servicenow_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

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
        try:
            stmt = select(Repository).where(
                Repository.ado_repo_id == ado_repo_id,
                Repository.ticket_id == ticket_id,
                Repository.is_active == 1,
            )
            result = await self._session.execute(stmt)
            return result.scalars().first()
        except SQLAlchemyError as db_exc:
            logger.error("Database error in get_repository_by_ado_repo_id_and_ticket", error=str(db_exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(db_exc),
                error_function="get_repository_by_ado_repo_id_and_ticket",
                error_file="src/repositories/servicenow_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise
        except Exception as exc:
            logger.error("Unexpected error in get_repository_by_ado_repo_id_and_ticket", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="get_repository_by_ado_repo_id_and_ticket",
                error_file="src/repositories/servicenow_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def update_repository(
        self,
        repository: Repository,
        repository_name: str,
        lead_approvers: str | None,
        modified_by: str,
    ) -> Repository:
        """Update an existing repository record."""
        try:
            repository.repository_name = repository_name
            repository.lead_approvers = lead_approvers
            repository.modified_at = datetime.utcnow()
            repository.modified_by = modified_by
            await self._session.flush()
            return repository
        except SQLAlchemyError as db_exc:
            logger.error("Database error in update_repository", error=str(db_exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(db_exc),
                error_function="update_repository",
                error_file="src/repositories/servicenow_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise
        except Exception as exc:
            logger.error("Unexpected error in update_repository", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="update_repository",
                error_file="src/repositories/servicenow_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def create_repository(self, repository: Repository) -> Repository:
        """Insert a new repository record into the database.

        Args:
            repository: The Repository ORM instance to persist.

        Returns:
            The persisted Repository instance.
        """
        try:
            self._session.add(repository)
            await self._session.flush()
            return repository
        except SQLAlchemyError as db_exc:
            logger.error("Database error in create_repository", error=str(db_exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(db_exc),
                error_function="create_repository",
                error_file="src/repositories/servicenow_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise
        except Exception as exc:
            logger.error("Unexpected error in create_repository", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="create_repository",
                error_file="src/repositories/servicenow_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def mark_project_onboarded(self, project: Project, modified_by: str) -> None:
        """Mark a project as DevSecOps onboarded.

        Args:
            project: The Project ORM instance to update.
            modified_by: The service account performing the update.
        """
        try:
            project.is_devsecops_onboarded = True
            project.modified_at = datetime.utcnow()
            project.modified_by = modified_by
            await self._session.flush()
        except SQLAlchemyError as db_exc:
            logger.error("Database error in mark_project_onboarded", error=str(db_exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(db_exc),
                error_function="mark_project_onboarded",
                error_file="src/repositories/servicenow_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise
        except Exception as exc:
            logger.error("Unexpected error in mark_project_onboarded", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="mark_project_onboarded",
                error_file="src/repositories/servicenow_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise
