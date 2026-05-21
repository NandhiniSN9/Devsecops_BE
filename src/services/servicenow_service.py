"""ServiceNow sync service for project and ticket ingestion."""

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
        self._repo = servicenow_repo

    async def sync_projects(self, request: SyncProjectRequest, created_by: str) -> dict:
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
                else:
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

            return {"created": created_count, "updated": updated_count, "total": len(request.projects)}
        except Exception as exc:
            logger.error("Error in sync_projects", error=str(exc))
            raise

    async def sync_single_devsecops_ticket(self, ticket_item: SyncDevSecOpsTicketItemRequest, created_by: str) -> dict:
        """Process a single DevSecOps ticket sync from ServiceNow."""
        try:
            success = await self._process_single_ticket(ticket_item, created_by)
            if success:
                return {"status": "created", "sn_project_id": ticket_item.sn_project_id}
            else:
                return {"status": "failed", "sn_project_id": ticket_item.sn_project_id}
        except Exception as exc:
            logger.error("Error in sync_single_devsecops_ticket", error=str(exc))
            raise

    async def sync_devsecops_tickets(self, request: SyncDevSecOpsTicketsRequest, created_by: str) -> dict:
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
                except Exception as exc:
                    failed_count += 1
                    logger.warning("Failed to process ticket", sn_project_id=ticket_item.sn_project_id, error=str(exc))

            return {"created": created_count, "failed": failed_count, "total": len(request.tickets)}
        except Exception as exc:
            logger.error("Error in sync_devsecops_tickets", error=str(exc))
            raise

    async def _process_single_ticket(self, ticket_item: SyncDevSecOpsTicketItemRequest, created_by: str) -> bool:
        try:
            # Step 1: Resolve project (auto-create if not found)
            project = await self._resolve_project(ticket_item, created_by)
            if not project:
                return False

            # Step 2: Check if ticket already exists (skip if both IDs are None)
            existing_ticket = None
            if ticket_item.sn_project_id or ticket_item.ado_project_id:
                existing_ticket = await self._repo.get_ticket_by_sn_or_devsec_id(
                    sn_project_id=ticket_item.sn_project_id,
                    devsec_project_id=ticket_item.ado_project_id,
                )

            if existing_ticket:
                await self._repo.update_ticket(
                    ticket=existing_ticket,
                    specialization_id=None,
                    project_id=project.project_id,
                    sn_project_id=ticket_item.sn_project_id,
                    devsec_project_id=ticket_item.ado_project_id,
                    project_name=ticket_item.ado_project_name,
                    project_type=ticket_item.project_type,
                    client=ticket_item.client,
                    requested_by=ticket_item.requested_by,
                    approver=None,
                    requested_at=ticket_item.requested_at,
                    modified_by=created_by,
                )
                ticket_id = existing_ticket.ticket_id
            else:
                # Get Inactive status for new ticket
                inactive_status = await self._repo.get_inactive_status()
                inactive_status_id = inactive_status.status_id if inactive_status else None

                ticket_id = uuid.uuid4()
                requested_at = ticket_item.requested_at.replace(tzinfo=None) if ticket_item.requested_at else None
                new_ticket = DevsecopsTicket(
                    ticket_id=ticket_id,
                    specialization_id=None,
                    project_id=project.project_id,
                    sn_project_id=ticket_item.sn_project_id,
                    devsec_project_id=ticket_item.ado_project_id,
                    project_name=ticket_item.ado_project_name,
                    project_type=ticket_item.project_type,
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

            # Step 3: Mark project as DevSecOps onboarded
            if not project.is_devsecops_onboarded:
                await self._repo.mark_project_onboarded(project, created_by)

            # Step 4: Process repositories
            if ticket_item.repositories:
                await self._process_repositories(ticket_item.repositories, ticket_id, created_by)

            return True
        except Exception as exc:
            logger.error("Error in _process_single_ticket", error=str(exc))
            raise

    async def _resolve_project(self, ticket_item: SyncDevSecOpsTicketItemRequest, created_by: str) -> Project | None:
        try:
            # Only lookup by sn_project_id if provided
            if ticket_item.sn_project_id:
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

            # No match found — fall back to the "Others" project
            others_project = await self._repo.get_others_project()
            if others_project:
                logger.info(
                    "No matching project found — linked to Others",
                    sn_project_id=ticket_item.sn_project_id,
                    project_name=ticket_item.ado_project_name,
                )
                return others_project

            logger.warning(
                "No matching project and no Others project found",
                sn_project_id=ticket_item.sn_project_id,
                project_name=ticket_item.ado_project_name,
            )
            return None
        except Exception as exc:
            logger.error("Error in _resolve_project", error=str(exc))
            raise

    async def _process_repositories(self, repositories: list, ticket_id: uuid.UUID, created_by: str) -> None:
        try:
            for repo_item in repositories:
                existing = None
                if repo_item.ado_repo_id:
                    existing = await self._repo.get_repository_by_ado_repo_id_and_ticket(
                        ado_repo_id=repo_item.ado_repo_id, ticket_id=ticket_id,
                    )

                specialization_csv = ",".join(repo_item.specialization) if repo_item.specialization else None
                approvers_csv = ",".join(repo_item.l1_approvers) if repo_item.l1_approvers else None

                if existing:
                    await self._repo.update_repository(
                        repository=existing,
                        repository_name=repo_item.ado_repo_name,
                        lead_approvers=approvers_csv,
                        specialization_name=specialization_csv,
                        modified_by=created_by,
                    )
                else:
                    new_repo = Repository(
                        repository_id=uuid.uuid4(),
                        ticket_id=ticket_id,
                        repository_name=repo_item.ado_repo_name,
                        ado_repo_id=repo_item.ado_repo_id,
                        specialization_name=specialization_csv,
                        lead_approvers=approvers_csv,
                        created_at=datetime.utcnow(),
                        created_by=created_by,
                        is_active=1,
                    )
                    await self._repo.create_repository(new_repo)
        except Exception as exc:
            logger.error("Error in _process_repositories", error=str(exc))
            raise
