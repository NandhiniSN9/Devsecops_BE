"""Service for retrieving filter dropdown options."""

import asyncio
import traceback

from sqlalchemy.exc import SQLAlchemyError
from src.models.response.filter_response import FilterItemResponse, FiltersDataResponse
from src.repositories.filters_repository import ClientRepository
from src.utils.logger import logger


class FilterService:
    """Business logic for the filters endpoint.

    Retrieves active specializations, distinct clients, and active statuses
    for populating dashboard filter dropdowns.
    """

    def __init__(self, client_repo: ClientRepository) -> None:
        """Initialize with repository dependency."""
        self._client_repo = client_repo

    async def get_filters(self) -> FiltersDataResponse:
        """Retrieve all filter dropdown options.

        Returns:
            FiltersDataResponse containing sorted specializations, clients, and statuses.
            Empty arrays are returned for categories with no active records.

        Raises:
            SQLAlchemyError: If database query fails.
            Exception: Re-raises unexpected errors after logging.
        """
        try:
            specializations_raw = await self._client_repo.get_active_specializations()
            specializations = [
                FilterItemResponse(
                    id=str(spec.specialization_id),
                    name=spec.specialization_name,
                )
                for spec in specializations_raw
            ]

            clients_raw = await self._client_repo.get_active_clients()
            clients = [
                FilterItemResponse(
                    id=item["client_id"],
                    name=item["client_name"],
                )
                for item in clients_raw
            ]

            statuses_raw = await self._client_repo.get_active_statuses()
            statuses = [
                FilterItemResponse(
                    id=str(status.status_id),
                    name=status.status_name,
                )
                for status in statuses_raw
            ]

            # Sort all arrays alphabetically by name (case-insensitive)
            specializations.sort(key=lambda item: item.name.lower())
            clients.sort(key=lambda item: item.name.lower())
            statuses.sort(key=lambda item: item.name.lower())

            return FiltersDataResponse(
                specializations=specializations,
                clients=clients,
                statuses=statuses,
            )

        except SQLAlchemyError as db_exc:
            logger.error("Database error retrieving filters", error=str(db_exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(db_exc),
                error_function="get_filters",
                error_file="src/services/filter_service.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise
        except Exception as exc:
            logger.error("Unexpected error retrieving filters", error=str(exc))
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="get_filters",
                error_file="src/services/filter_service.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise
