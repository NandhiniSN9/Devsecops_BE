"""Service for retrieving filter dropdown options."""

from src.dtos.response.filter_response import FilterItemResponse, FiltersDataResponse
from src.repositories.filters_repository import ClientRepository


class FilterService:
    """Business logic for the filters endpoint.

    Retrieves active specializations, distinct clients, and active statuses
    for populating dashboard filter dropdowns.
    """

    def __init__(
        self,
        client_repo: ClientRepository,
    ) -> None:
        self._client_repo = client_repo

    async def get_filters(self) -> FiltersDataResponse:
        """Retrieve all filter dropdown options.

        Returns:
            FiltersDataResponse containing sorted specializations, clients, and statuses.
            Empty arrays are returned for categories with no active records.
        """
        # Query all active specializations
        specializations_raw = await self._client_repo.get_active_specializations()
        specializations = [
            FilterItemResponse(
                id=str(spec.specialization_id),
                name=spec.specialization_name,
            )
            for spec in specializations_raw
        ]

        # Query distinct non-null, non-empty clients from active projects
        clients_raw = await self._client_repo.get_active_clients()
        clients = [
            FilterItemResponse(
                id=item["client_id"],
                name=item["client_name"],
            )
            for item in clients_raw
        ]

        # Query all active statuses
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
