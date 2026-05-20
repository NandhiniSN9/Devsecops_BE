"""Repository for client-facing lookup data access operations.

Consolidates specialization, status, and client queries into a single
repository since they all serve as filter/dropdown data for the frontend.
"""

import asyncio
import traceback
import uuid
from sqlalchemy import String, distinct, func, select, union
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from src.repositories.schema.devsecops_ticket import DevsecopsTicket
from src.repositories.schema.project import Project
from src.repositories.schema.specialization import Specialization
from src.repositories.schema.status import Status
from src.settings import CLIENT_UUID_NAMESPACE
from src.utils.logger import logger


class ClientRepository:
    """Data access layer for client-facing lookup queries.

    Provides access to specializations, statuses, and clients
    used for filter dropdowns and lookup operations.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_active_specializations(self) -> list[Specialization]:
        """Return all specializations where is_active = 1."""
        try:
            stmt = select(Specialization).where(Specialization.is_active == 1)
            result = await self._session.execute(stmt)
            return list(result.scalars().all())
        except SQLAlchemyError as db_exc:
            logger.error("Database error in get_active_specializations", error=str(db_exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(db_exc),
                error_function="get_active_specializations",
                error_file="src/repositories/filters_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise
        except Exception as exc:
            logger.error("Unexpected error in get_active_specializations", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="get_active_specializations",
                error_file="src/repositories/filters_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def get_active_statuses(self) -> list[Status]:
        """Return all statuses where is_active = 1."""
        try:
            stmt = select(Status).where(Status.is_active == 1)
            result = await self._session.execute(stmt)
            return list(result.scalars().all())
        except SQLAlchemyError as db_exc:
            logger.error("Database error in get_active_statuses", error=str(db_exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(db_exc),
                error_function="get_active_statuses",
                error_file="src/repositories/filters_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise
        except Exception as exc:
            logger.error("Unexpected error in get_active_statuses", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="get_active_statuses",
                error_file="src/repositories/filters_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise

    async def get_active_clients(self) -> list[dict]:
        """Get distinct non-null, non-empty client values from active projects and devsecops_tickets.

        Combines clients from both the projects table and the devsecops_tickets table
        to ensure the filter dropdown shows all known clients.

        Returns:
            List of dicts with 'client_id' (UUID v5) and 'client_name' keys,
            sorted alphabetically by client_name.
        """
        try:
            # Clients from projects
            projects_clients = (
                select(Project.client.label("client_name"))
                .where(Project.is_active == 1)
                .where(Project.client.isnot(None))
                .where(Project.client != "")
                .where(func.trim(Project.client.cast(String)) != "")
            )

            # Clients from devsecops_tickets
            tickets_clients = (
                select(DevsecopsTicket.client.label("client_name"))
                .where(DevsecopsTicket.is_active == 1)
                .where(DevsecopsTicket.client.isnot(None))
                .where(DevsecopsTicket.client != "")
                .where(func.trim(DevsecopsTicket.client.cast(String)) != "")
            )

            # Union both sources and get distinct values
            combined = union(projects_clients, tickets_clients).subquery()
            stmt = select(distinct(combined.c.client_name)).order_by(combined.c.client_name.asc())

            result = await self._session.execute(stmt)
            rows = result.scalars().all()

            return [
                {
                    "client_id": str(uuid.uuid5(CLIENT_UUID_NAMESPACE, client_name)),
                    "client_name": client_name,
                }
                for client_name in rows
            ]
        except SQLAlchemyError as db_exc:
            logger.error("Database error in get_active_clients", error=str(db_exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(db_exc),
                error_function="get_active_clients",
                error_file="src/repositories/filters_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise
        except Exception as exc:
            logger.error("Unexpected error in get_active_clients", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="get_active_clients",
                error_file="src/repositories/filters_repository.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise
