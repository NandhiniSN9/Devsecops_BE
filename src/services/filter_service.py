"""Service for retrieving filter dropdown options."""

import uuid

from src.models.filter_models import FilterItem, FiltersData
from src.repositories.project_repository import ProjectRepository
from src.repositories.specialization_repository import SpecializationRepository
from src.repositories.status_repository import StatusRepository
from src.settings import CLIENT_UUID_NAMESPACE


class FilterService:
    """Business logic for the filters endpoint.

    Retrieves active specializations, distinct clients, and active statuses
    for populating dashboard filter dropdowns.
    """

    def __init__(
        self,
        specialization_repo: SpecializationRepository,
        project_repo: ProjectRepository,
        status_repo: StatusRepository,
    ) -> None:
        self._specialization_repo = specialization_repo
        self._project_repo = project_repo
        self._status_repo = status_repo

    async def get_filters(self) -> FiltersData:
        """Retrieve all filter dropdown options.

        Returns:
            FiltersData containing sorted specializations, clients, and statuses.
            Empty arrays are returned for categories with no active records.
        """
        # Query all active specializations
        specializations_raw = await self._specialization_repo.get_active_specializations()
        specializations = [
            FilterItem(
                id=str(spec.specialization_id),
                name=spec.specialization_name,
            )
            for spec in specializations_raw
        ]

        # Query distinct non-null, non-empty clients from active projects
        clients_raw = await self._project_repo.get_distinct_clients()
        clients = [
            FilterItem(
                id=str(uuid.uuid5(CLIENT_UUID_NAMESPACE, client_name)),
                name=client_name,
            )
            for client_name in clients_raw
        ]

        # Query all active statuses
        statuses_raw = await self._status_repo.get_active_statuses()
        statuses = [
            FilterItem(
                id=str(status.status_id),
                name=status.status_name,
            )
            for status in statuses_raw
        ]

        # Sort all arrays alphabetically by name (case-insensitive)
        specializations.sort(key=lambda item: item.name.lower())
        clients.sort(key=lambda item: item.name.lower())
        statuses.sort(key=lambda item: item.name.lower())

        return FiltersData(
            specializations=specializations,
            clients=clients,
            statuses=statuses,
        )
