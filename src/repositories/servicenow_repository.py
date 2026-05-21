"""Repository for ServiceNow sync data access operations."""

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
        try:
            stmt = select(Project).where(Project.sn_project_id == sn_project_id, Project.is_active == 1)
            result = await self._session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as exc:
            logger.error("Error in get_project_by_sn_project_id", error=str(exc))
            raise

    async def get_project_by_name(self, project_name: str) -> Project | None:
        try:
            stmt = select(Project).where(func.lower(Project.project_name) == func.lower(project_name), Project.is_active == 1)
            result = await self._session.execute(stmt)
            return result.scalars().first()
        except Exception as exc:
            logger.error("Error in get_project_by_name", error=str(exc))
            raise

    async def get_project_by_client(self, client: str) -> Project | None:
        try:
            stmt = select(Project).where(func.lower(Project.client) == func.lower(client), Project.is_active == 1)
            result = await self._session.execute(stmt)
            return result.scalars().first()
        except Exception as exc:
            logger.error("Error in get_project_by_client", error=str(exc))
            raise

    async def get_project_by_normalized_name(self, ticket_project_name: str) -> Project | None:
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
        except Exception as exc:
            logger.error("Error in get_project_by_normalized_name", error=str(exc))
            raise

    async def get_others_project(self) -> Project | None:
        try:
            stmt = select(Project).where(func.lower(Project.project_name) == "others", Project.is_active == 1)
            result = await self._session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as exc:
            logger.error("Error in get_others_project", error=str(exc))
            raise

    async def get_inactive_status(self) -> Status | None:
        try:
            stmt = select(Status).where(func.lower(Status.status_name) == "inactive", Status.is_active == 1)
            result = await self._session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as exc:
            logger.error("Error in get_inactive_status", error=str(exc))
            raise

    async def create_project(self, project: Project) -> Project:
        try:
            self._session.add(project)
            await self._session.flush()
            return project
        except Exception as exc:
            logger.error("Error in create_project", error=str(exc))
            raise

    async def update_project(self, project: Project, project_name: str, onboarded_date, project_type: str, specialization_name: str | None, is_applicable: bool, client: str | None, modified_by: str) -> Project:
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
        except Exception as exc:
            logger.error("Error in update_project", error=str(exc))
            raise

    async def create_ticket(self, ticket: DevsecopsTicket) -> DevsecopsTicket:
        try:
            self._session.add(ticket)
            await self._session.flush()
            return ticket
        except Exception as exc:
            logger.error("Error in create_ticket", error=str(exc))
            raise

    async def get_ticket_by_sn_or_devsec_id(self, sn_project_id: str | None, devsec_project_id: str | None) -> DevsecopsTicket | None:
        try:
            conditions = []
            if sn_project_id:
                conditions.append(DevsecopsTicket.sn_project_id == sn_project_id)
            if devsec_project_id:
                conditions.append(DevsecopsTicket.devsec_project_id == devsec_project_id)
            if not conditions:
                return None
            stmt = select(DevsecopsTicket).where(or_(*conditions), DevsecopsTicket.is_active == 1)
            result = await self._session.execute(stmt)
            return result.scalars().first()
        except Exception as exc:
            logger.error("Error in get_ticket_by_sn_or_devsec_id", error=str(exc))
            raise

    async def update_ticket(self, ticket: DevsecopsTicket, specialization_id, project_id, sn_project_id, devsec_project_id, project_name, project_type, client, requested_by, approver, requested_at, modified_by: str) -> DevsecopsTicket:
        try:
            ticket.specialization_name = specialization_name
            ticket.project_id = project_id
            ticket.sn_project_id = sn_project_id
            ticket.devsec_project_id = devsec_project_id
            ticket.project_name = project_name
            ticket.project_type = project_type
            ticket.client = client
            ticket.requested_by = requested_by
            ticket.approver = approver
            ticket.requested_at = requested_at.replace(tzinfo=None) if requested_at else None
            ticket.modified_at = datetime.utcnow()
            ticket.modified_by = modified_by
            await self._session.flush()
            return ticket
        except Exception as exc:
            logger.error("Error in update_ticket", error=str(exc))
            raise

    async def get_repository_by_ado_repo_id_and_ticket(self, ado_repo_id: str, ticket_id: uuid.UUID) -> Repository | None:
        try:
            stmt = select(Repository).where(Repository.ado_repo_id == ado_repo_id, Repository.ticket_id == ticket_id, Repository.is_active == 1)
            result = await self._session.execute(stmt)
            return result.scalars().first()
        except Exception as exc:
            logger.error("Error in get_repository_by_ado_repo_id_and_ticket", error=str(exc))
            raise

    async def update_repository(self, repository: Repository, repository_name: str, lead_approvers: str | None, specialization_name: str | None, modified_by: str) -> Repository:
        try:
            repository.repository_name = repository_name
            repository.lead_approvers = lead_approvers
            repository.specialization_name = specialization_name
            repository.modified_at = datetime.utcnow()
            repository.modified_by = modified_by
            await self._session.flush()
            return repository
        except Exception as exc:
            logger.error("Error in update_repository", error=str(exc))
            raise

    async def create_repository(self, repository: Repository) -> Repository:
        try:
            self._session.add(repository)
            await self._session.flush()
            return repository
        except Exception as exc:
            logger.error("Error in create_repository", error=str(exc))
            raise

    async def mark_project_onboarded(self, project: Project, modified_by: str) -> None:
        try:
            project.is_devsecops_onboarded = True
            project.modified_at = datetime.utcnow()
            project.modified_by = modified_by
            await self._session.flush()
        except Exception as exc:
            logger.error("Error in mark_project_onboarded", error=str(exc))
            raise
