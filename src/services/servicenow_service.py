"""ServiceNow sync service for project and ticket ingestion.

Implements the business logic for:
- Project sync with deduplication by sn_project_id
- DevSecOps ticket sync with 5-step project resolution fallback
- Partial success handling for batch ticket processing
"""

import uuid
from datetime import datetime

from sqlalchemy.exc import SQLAlchemyError

from src.models.request.servicenow_request import (
    SyncDevSecOpsTicketItemRequest,
    SyncDevSecOpsTicketsRequest,
    SyncProjectRequest,
)
from src.repositories.schema.devsecops_ticket import DevsecopsTicket
from src.repositories.schema.project import Project
from src.repositories.schema.repository import Repository
from src.repositories.servicenow_repository import ServiceNowRepository
from src.settings import SERVICENOW_SYNC_METHOD
from src.utils.exceptions.exceptions import InvalidParameterError
from src.utils.logger import logger


class ServiceNowService:
    """Service for processing ServiceNow sync operations."""

    def __init__(self, servicenow_repo: ServiceNowRepository) -> None:
        """Initialize with repository dependency."""
        self._repo = servicenow_repo

    async def sync_projects(self, request: SyncProjectRequest, created_by: str) -> dict:
        """Process project sync from ServiceNow."""
        try:
            inactive_status = await self._repo.get_inactive_status()
            inactive_status_id = inactive_status.status_id if inactive_status else None

            created_count = 0
            updated_count = 0

            for project_item in request.projects:
                existing = await self._repo.get_project_by_sn_project_id(project_item.sn_project_id)

                if existing:
                    await self._repo.update_project(
                        project=existing,
                        project_name=project_item.project_name,
                        onboarded_date=project_item.onboarded_date,
                        project_type=project_item.project_type,
                        specialization_name=project_item.specialization_name,
                        is_applicable=project_item.is_applicable,
                        client=project_item.client,
                        modified_by=created_by,
                    )
                    updated_count += 1
                    logger.info("Project updated", sn_project_id=project_item.sn_project_id)
                    continue

                new_project = Project(
                    project_id=uuid.uuid4(),
                    status_id=inactive_status_id,
                    sn_project_id=project_item.sn_project_id,
                    project_name=project_item.project_name,
                    onboarded_date=project_item.onboarded_date,
                    project_type=project_item.project_type,
                    specialization_name=project_item.specialization_name,
                    is_applicable=project_item.is_applicable,
                    client=project_item.client,
                    created_at=datetime.utcnow(),
                    created_by=created_by,
                    is_active=1,
                )
                await self._repo.create_project(new_project)
                created_count += 1
                logger.info("Project created", sn_project_id=project_item.sn_project_id)

            return {"created": created_count, "updated": updated_count, "total": len(request.projects)}

        except SQLAlchemyError as db_exc:
            logger.error("Database error during project sync", error=str(db_exc))
            raise
        except InvalidParameterError:
            raise
        except Exception as exc:
            logger.error("Unexpected error during project sync", error=str(exc))
            raise

    async def sync_devsecops_tickets(self, request: SyncDevSecOpsTicketsRequest, created_by: str) -> dict:
        """Process DevSecOps ticket sync from ServiceNow."""
        try:
            created_count = 0
            failed_count = 0

            for ticket_item in request.tickets:
                try:
                    success = await self._process_single_ticket(ticket_item, created_by)
                    if success:
                        created_count += 1
                    else:
                        failed_count += 1
                except SQLAlchemyError as db_exc:
                    failed_count += 1
                    logger.warning("DB error processing ticket", sn_project_id=ticket_item.sn_project_id, error=str(db_exc))
                except Exception as exc:
                    failed_count += 1
                    logger.warning("Failed to process ticket", sn_project_id=ticket_item.sn_project_id, error=str(exc))

            return {"created": created_count, "failed": failed_count, "total": len(request.tickets)}

        except Exception as exc:
            logger.error("Unexpected error during ticket sync", error=str(exc))
            raise

    async def _process_single_ticket(self, ticket_item: SyncDevSecOpsTicketItemRequest, created_by: str) -> bool:
        """Process a single DevSecOps ticket (upsert)."""
        try:
            # Step 1: Resolve specialization from first repository's first specialization
            specialization_name = self._extract_specialization(ticket_item)
            specialization = None
            if specialization_name:
                specialization = await self._repo.get_specialization_by_name(specialization_name)

            if not specialization:
                logger.warning("Specialization not found, skipping ticket", sn_project_id=ticket_item.sn_project_id)
                return False

            # Step 2: Resolve project (5-step fallback + auto-create)
            project = await self._resolve_project(ticket_item, created_by)
            if not project:
                logger.warning("No project found, skipping ticket", sn_project_id=ticket_item.sn_project_id)
                return False

            # Step 3: Check if ticket already exists
            existing_ticket = await self._repo.get_ticket_by_sn_or_devsec_id(
                sn_project_id=ticket_item.sn_project_id,
                devsec_project_id=ticket_item.ado_project_id,
            )

            if existing_ticket:
                await self._repo.update_ticket(
                    ticket=existing_ticket,
                    specialization_id=specialization.specialization_id,
                    project_id=project.project_id,
                    sn_project_id=project.sn_project_id,
                    devsec_project_id=ticket_item.ado_project_id,
                    project_name=ticket_item.ado_project_name,
                    client=ticket_item.client,
                    requested_by=ticket_item.requested_by,
                    approver=None,
                    requested_at=ticket_item.requested_at,
                    modified_by=created_by,
                )
                ticket_id = existing_ticket.ticket_id
                logger.info("Ticket updated", ticket_id=str(ticket_id), sn_project_id=ticket_item.sn_project_id)
            else:
                ticket_id = uuid.uuid4()
                requested_at = ticket_item.requested_at.replace(tzinfo=None) if ticket_item.requested_at else None
                new_ticket = DevsecopsTicket(
                    ticket_id=ticket_id,
                    specialization_id=specialization.specialization_id,
                    project_id=project.project_id,
                    sn_project_id=project.sn_project_id,
                    devsec_project_id=ticket_item.ado_project_id,
                    project_name=ticket_item.ado_project_name,
                    client=ticket_item.client,
                    requested_by=ticket_item.requested_by,
                    approver=None,
                    sync_method=SERVICENOW_SYNC_METHOD,
                    requested_at=requested_at,
                    created_at=datetime.utcnow(),
                    created_by=created_by,
                    is_active=1,
                )
                await self._repo.create_ticket(new_ticket)
                logger.info("Ticket created", ticket_id=str(ticket_id), sn_project_id=ticket_item.sn_project_id)

            # Step 4: Mark project as DevSecOps onboarded
            if not project.is_devsecops_onboarded:
                await self._repo.mark_project_onboarded(project, created_by)

            # Step 5: Process repositories (upsert)
            if ticket_item.repositories:
                await self._process_repositories(ticket_item.repositories, ticket_id, created_by)

            return True

        except SQLAlchemyError as db_exc:
            logger.error("Database error in _process_single_ticket", error=str(db_exc))
            raise
        except Exception as exc:
            logger.error("Unexpected error in _process_single_ticket", error=str(exc))
            raise

    async def _resolve_project(self, ticket_item: SyncDevSecOpsTicketItemRequest, created_by: str) -> Project | None:
        """Resolve project using 5-step fallback logic. If no match, auto-create a new project."""
        try:
            project = await self._repo.get_project_by_sn_project_id(ticket_item.sn_project_id)
            if project:
                return project

            project = await self._repo.get_project_by_name(ticket_item.ado_project_name)
            if project:
                return project

            project = await self._repo.get_project_by_normalized_name(ticket_item.ado_project_name)
            if project:
                return project

            if ticket_item.client:
                project = await self._repo.get_project_by_client(ticket_item.client)
                if project:
                    return project

            # Step 6: Auto-create new project with Inactive status
            inactive_status = await self._repo.get_inactive_status()
            inactive_status_id = inactive_status.status_id if inactive_status else None

            new_project = Project(
                project_id=uuid.uuid4(),
                status_id=inactive_status_id,
                sn_project_id=ticket_item.sn_project_id,
                project_name=ticket_item.ado_project_name,
                onboarded_date=datetime.utcnow().date(),
                project_type=ticket_item.project_type or "Application",
                client=ticket_item.client,
                created_at=datetime.utcnow(),
                created_by=created_by,
                is_active=1,
            )
            await self._repo.create_project(new_project)
            logger.info("Auto-created project", sn_project_id=ticket_item.sn_project_id, project_name=ticket_item.ado_project_name)
            return new_project

        except Exception as exc:
            logger.error("Error in _resolve_project", error=str(exc))
            raise

    async def _process_repositories(
        self,
        repositories: list,
        ticket_id: uuid.UUID,
        created_by: str,
    ) -> None:
        """Process repository records for a ticket (upsert by ado_repo_id)."""
        try:
            for repo_item in repositories:
                existing = None

                if repo_item.ado_repo_id:
                    existing = await self._repo.get_repository_by_ado_repo_id_and_ticket(
                        ado_repo_id=repo_item.ado_repo_id,
                        ticket_id=ticket_id,
                    )

                if existing:
                    await self._repo.update_repository(
                        repository=existing,
                        repository_name=repo_item.ado_repo_name,
                        lead_approvers=",".join(repo_item.l1_approvers) if repo_item.l1_approvers else None,
                        modified_by=created_by,
                    )
                    logger.info("Repository updated", repo_name=repo_item.ado_repo_name, ticket_id=str(ticket_id))
                else:
                    new_repo = Repository(
                        repository_id=uuid.uuid4(),
                        ticket_id=ticket_id,
                        repository_name=repo_item.ado_repo_name,
                        ado_repo_id=repo_item.ado_repo_id,
                        lead_approvers=",".join(repo_item.l1_approvers) if repo_item.l1_approvers else None,
                        created_at=datetime.utcnow(),
                        created_by=created_by,
                        is_active=1,
                    )
                    await self._repo.create_repository(new_repo)
                    logger.info("Repository created", repo_name=repo_item.ado_repo_name, ticket_id=str(ticket_id))

        except Exception as exc:
            logger.error("Error in _process_repositories", error=str(exc))
            raise

    @staticmethod
    def _extract_specialization(ticket_item: SyncDevSecOpsTicketItemRequest) -> str | None:
        """Extract the first specialization name from the ticket's repositories.

        Specialization is now at the repository level (array). We use the first
        repository's first specialization for ticket-level resolution.

        Args:
            ticket_item: The ticket data.

        Returns:
            First specialization name found, or None.
        """
        if ticket_item.repositories:
            for repo in ticket_item.repositories:
                if repo.specialization and len(repo.specialization) > 0:
                    return repo.specialization[0]
        return None
