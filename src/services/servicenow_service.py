"""ServiceNow sync service for project and ticket ingestion.

Implements the business logic for:
- Project sync with deduplication by sn_project_id
- DevSecOps ticket sync with 4-step project resolution fallback
- Partial success handling for batch ticket processing
"""

import uuid
from datetime import datetime

from src.models.servicenow_models import (
    SyncDevSecOpsTicketItem,
    SyncDevSecOpsTicketsRequest,
    SyncProjectRequest,
)
from src.repositories.schema.devsecops_ticket import DevsecopsTicket
from src.repositories.schema.project import Project
from src.repositories.schema.repository import Repository
from src.repositories.servicenow_repository import ServiceNowRepository
from src.settings import SERVICENOW_SYNC_METHOD
from src.utils.logger import logger


class ServiceNowService:
    """Service for processing ServiceNow sync operations.

    Handles project ingestion with deduplication and ticket ingestion
    with 4-step project resolution fallback and partial success.
    """

    def __init__(self, servicenow_repo: ServiceNowRepository) -> None:
        """Initialize with repository dependency."""
        self._repo = servicenow_repo

    async def sync_projects(self, request: SyncProjectRequest, created_by: str) -> dict:
        """Process project sync from ServiceNow.

        For each project in the request:
        - If sn_project_id already exists → skip (no duplicate)
        - If not found → create new project with Inactive status

        Args:
            request: Validated SyncProjectRequest payload.
            created_by: The authenticated service account identifier.

        Returns:
            Dict with sync result summary.
        """
        # Look up the Inactive status once
        inactive_status = await self._repo.get_inactive_status()
        inactive_status_id = inactive_status.status_id if inactive_status else None

        created_count = 0
        updated_count = 0

        for project_item in request.projects:
            existing = await self._repo.get_project_by_sn_project_id(project_item.sn_project_id)

            if existing:
                # Update existing project with incoming details
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
                logger.info(
                    "Project updated successfully",
                    sn_project_id=project_item.sn_project_id,
                    project_name=project_item.project_name,
                    project_id=str(existing.project_id),
                )
                continue

            # Create new project record
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

            logger.info(
                "Project created successfully",
                sn_project_id=project_item.sn_project_id,
                project_name=project_item.project_name,
                project_id=str(new_project.project_id),
            )

        await self._repo.commit()

        logger.info(
            "Project sync completed",
            created=created_count,
            updated=updated_count,
            total=len(request.projects),
        )

        return {
            "created": created_count,
            "updated": updated_count,
            "total": len(request.projects),
        }

    async def sync_devsecops_tickets(self, request: SyncDevSecOpsTicketsRequest, created_by: str) -> dict:
        """Process DevSecOps ticket sync from ServiceNow.

        For each ticket:
        - Resolve specialization by name
        - Resolve project via 4-step fallback
        - Create ticket record
        - Create repository records (skip duplicates)

        Supports partial success — valid tickets are processed while
        invalid ones are logged and skipped.

        Args:
            request: Validated SyncDevSecOpsTicketsRequest payload.
            created_by: The authenticated service account identifier.

        Returns:
            Dict with sync result summary.
        """
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
                logger.warning(
                    "Failed to process ticket",
                    sn_project_id=ticket_item.sn_project_id,
                    project_name=ticket_item.project_name,
                    error=str(exc),
                )

        await self._repo.commit()

        logger.info(
            "DevSecOps tickets sync completed",
            created=created_count,
            failed=failed_count,
            total=len(request.tickets),
        )

        return {
            "created": created_count,
            "failed": failed_count,
            "total": len(request.tickets),
        }

    async def _process_single_ticket(self, ticket_item: SyncDevSecOpsTicketItem, created_by: str) -> bool:
        """Process a single DevSecOps ticket (upsert).

        If a ticket with the same sn_project_id or devSec_project_id exists,
        update it. Otherwise, create a new ticket.

        Args:
            ticket_item: The ticket data to process.
            created_by: The authenticated service account identifier.

        Returns:
            True if the ticket was successfully created/updated, False otherwise.
        """
        # Step 1: Resolve specialization
        specialization = await self._repo.get_specialization_by_name(ticket_item.specialization_name)
        if not specialization:
            logger.warning(
                "Specialization not found, skipping ticket",
                specialization_name=ticket_item.specialization_name,
                sn_project_id=ticket_item.sn_project_id,
            )
            return False

        # Step 2: Resolve project (4-step fallback)
        project = await self._resolve_project(ticket_item)
        if not project:
            logger.warning(
                "No project found (including default), skipping ticket",
                sn_project_id=ticket_item.sn_project_id,
                project_name=ticket_item.project_name,
            )
            return False

        # Step 3: Check if ticket already exists (by sn_project_id or devSec_project_id)
        existing_ticket = await self._repo.get_ticket_by_sn_or_devsec_id(
            sn_project_id=ticket_item.sn_project_id,
            devsec_project_id=ticket_item.devsec_project_id,
        )

        if existing_ticket:
            # Update existing ticket
            await self._repo.update_ticket(
                ticket=existing_ticket,
                specialization_id=specialization.specialization_id,
                project_id=project.project_id,
                sn_project_id=project.sn_project_id,
                devsec_project_id=ticket_item.devsec_project_id,
                project_name=ticket_item.project_name,
                client=ticket_item.client,
                requested_by=ticket_item.requested_by,
                approver=ticket_item.approver,
                requested_at=ticket_item.requested_at,
                modified_by=created_by,
            )
            ticket_id = existing_ticket.ticket_id
            logger.info(
                "Ticket updated successfully",
                ticket_id=str(ticket_id),
                sn_project_id=ticket_item.sn_project_id,
                specialization=ticket_item.specialization_name,
            )
        else:
            # Create new ticket
            ticket_id = uuid.uuid4()
            # Strip timezone info to match TIMESTAMP WITHOUT TIME ZONE column
            requested_at = ticket_item.requested_at.replace(tzinfo=None) if ticket_item.requested_at else None
            new_ticket = DevsecopsTicket(
                ticket_id=ticket_id,
                specialization_id=specialization.specialization_id,
                project_id=project.project_id,
                sn_project_id=project.sn_project_id,
                devsec_project_id=ticket_item.devsec_project_id,
                project_name=ticket_item.project_name,
                client=ticket_item.client,
                requested_by=ticket_item.requested_by,
                approver=ticket_item.approver,
                sync_method=SERVICENOW_SYNC_METHOD,
                requested_at=requested_at,
                created_at=datetime.utcnow(),
                created_by=created_by,
                is_active=1,
            )
            await self._repo.create_ticket(new_ticket)
            logger.info(
                "Ticket created successfully",
                ticket_id=str(ticket_id),
                sn_project_id=ticket_item.sn_project_id,
                specialization=ticket_item.specialization_name,
            )

        # Step 4: Process repositories (upsert)
        if ticket_item.repositories:
            await self._process_repositories(ticket_item.repositories, ticket_id, created_by)

        return True

    async def _resolve_project(self, ticket_item: SyncDevSecOpsTicketItem) -> Project | None:
        """Resolve project using 4-step fallback logic.

        1. Match by sn_project_id
        2. Match by project_name
        3. Match by client
        4. Use default project

        Args:
            ticket_item: The ticket data containing resolution fields.

        Returns:
            The resolved Project, or None if no default project exists.
        """
        # Step 1: Match by sn_project_id
        project = await self._repo.get_project_by_sn_project_id(ticket_item.sn_project_id)
        if project:
            return project

        # Step 2: Match by project_name
        project = await self._repo.get_project_by_name(ticket_item.project_name)
        if project:
            return project

        # Step 3: Match by client
        if ticket_item.client:
            project = await self._repo.get_project_by_client(ticket_item.client)
            if project:
                return project

        # Step 4: Use default project
        project = await self._repo.get_default_project()
        return project

    async def _process_repositories(
        self,
        repositories: list,
        ticket_id: uuid.UUID,
        created_by: str,
    ) -> None:
        """Process repository records for a ticket (upsert by ado_repo_id).

        If a repo with the same ado_repo_id exists for the ticket, update it.
        If different or new, create a new repo record.

        Args:
            repositories: List of RepositoryItem objects.
            ticket_id: The ticket UUID to link repositories to.
            created_by: The authenticated service account identifier.
        """
        for repo_item in repositories:
            existing = None

            # Check by ado_repo_id if provided
            if repo_item.ado_repo_id:
                existing = await self._repo.get_repository_by_ado_repo_id_and_ticket(
                    ado_repo_id=repo_item.ado_repo_id,
                    ticket_id=ticket_id,
                )

            if existing:
                # Update existing repository
                await self._repo.update_repository(
                    repository=existing,
                    repository_name=repo_item.repo_name,
                    lead_approvers=",".join(repo_item.lead_approvers) if repo_item.lead_approvers else None,
                    modified_by=created_by,
                )
                logger.info(
                    "Repository updated",
                    repo_name=repo_item.repo_name,
                    ado_repo_id=repo_item.ado_repo_id,
                    ticket_id=str(ticket_id),
                )
            else:
                # Create new repository
                new_repo = Repository(
                    repository_id=uuid.uuid4(),
                    ticket_id=ticket_id,
                    repository_name=repo_item.repo_name,
                    ado_repo_id=repo_item.ado_repo_id,
                    lead_approvers=",".join(repo_item.lead_approvers) if repo_item.lead_approvers else None,
                    created_at=datetime.utcnow(),
                    created_by=created_by,
                    is_active=1,
                )
                await self._repo.create_repository(new_repo)
                logger.info(
                    "Repository created",
                    repo_name=repo_item.repo_name,
                    ado_repo_id=repo_item.ado_repo_id,
                    ticket_id=str(ticket_id),
                )

            logger.info(
                "Repository created",
                repo_name=repo_item.repo_name,
                ticket_id=str(ticket_id),
            )
