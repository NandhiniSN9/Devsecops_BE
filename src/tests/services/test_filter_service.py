"""Unit tests for FilterService."""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.models.filter_models import FiltersData
from src.repositories.project_repository import ProjectRepository
from src.repositories.specialization_repository import SpecializationRepository
from src.repositories.status_repository import StatusRepository
from src.services.filter_service import FilterService
from src.settings import CLIENT_UUID_NAMESPACE


@pytest.fixture
def mock_specialization_repo():
    """Create a mock SpecializationRepository."""
    repo = AsyncMock(spec=SpecializationRepository)
    return repo


@pytest.fixture
def mock_project_repo():
    """Create a mock ProjectRepository."""
    repo = AsyncMock(spec=ProjectRepository)
    return repo


@pytest.fixture
def mock_status_repo():
    """Create a mock StatusRepository."""
    repo = AsyncMock(spec=StatusRepository)
    return repo


@pytest.fixture
def filter_service(mock_specialization_repo, mock_project_repo, mock_status_repo):
    """Create a FilterService with mocked repositories."""
    return FilterService(
        specialization_repo=mock_specialization_repo,
        project_repo=mock_project_repo,
        status_repo=mock_status_repo,
    )


def _make_specialization(spec_id: uuid.UUID, name: str) -> MagicMock:
    """Helper to create a mock Specialization ORM object."""
    spec = MagicMock()
    spec.specialization_id = spec_id
    spec.specialization_name = name
    return spec


def _make_status(status_id: uuid.UUID, name: str) -> MagicMock:
    """Helper to create a mock Status ORM object."""
    status = MagicMock()
    status.status_id = status_id
    status.status_name = name
    return status


class TestGetFiltersAllCategoriesPopulated:
    """Tests for FilterService.get_filters when all categories have data."""

    async def test_returns_all_active_specializations(
        self, filter_service, mock_specialization_repo, mock_project_repo, mock_status_repo
    ):
        """Test that active specializations are mapped to FilterItem objects correctly."""
        spec_id = uuid.uuid4()
        mock_specialization_repo.get_active_specializations.return_value = [
            _make_specialization(spec_id, "Backend"),
        ]
        mock_project_repo.get_distinct_clients.return_value = []
        mock_status_repo.get_active_statuses.return_value = []

        result = await filter_service.get_filters()

        assert len(result.specializations) == 1
        assert result.specializations[0].id == str(spec_id)
        assert result.specializations[0].name == "Backend"

    async def test_returns_all_active_clients_with_uuid5_ids(
        self, filter_service, mock_specialization_repo, mock_project_repo, mock_status_repo
    ):
        """Test that clients are mapped with deterministic UUID v5 IDs."""
        mock_specialization_repo.get_active_specializations.return_value = []
        mock_project_repo.get_distinct_clients.return_value = ["Acme Corp", "Beta Inc"]
        mock_status_repo.get_active_statuses.return_value = []

        result = await filter_service.get_filters()

        assert len(result.clients) == 2
        expected_id_acme = str(uuid.uuid5(CLIENT_UUID_NAMESPACE, "Acme Corp"))
        expected_id_beta = str(uuid.uuid5(CLIENT_UUID_NAMESPACE, "Beta Inc"))
        assert result.clients[0].id == expected_id_acme
        assert result.clients[0].name == "Acme Corp"
        assert result.clients[1].id == expected_id_beta
        assert result.clients[1].name == "Beta Inc"

    async def test_returns_all_active_statuses(
        self, filter_service, mock_specialization_repo, mock_project_repo, mock_status_repo
    ):
        """Test that active statuses are mapped to FilterItem objects correctly."""
        status_id = uuid.uuid4()
        mock_specialization_repo.get_active_specializations.return_value = []
        mock_project_repo.get_distinct_clients.return_value = []
        mock_status_repo.get_active_statuses.return_value = [
            _make_status(status_id, "Active"),
        ]

        result = await filter_service.get_filters()

        assert len(result.statuses) == 1
        assert result.statuses[0].id == str(status_id)
        assert result.statuses[0].name == "Active"

    async def test_returns_filters_data_type(
        self, filter_service, mock_specialization_repo, mock_project_repo, mock_status_repo
    ):
        """Test that the return type is FiltersData."""
        mock_specialization_repo.get_active_specializations.return_value = [
            _make_specialization(uuid.uuid4(), "DevOps"),
        ]
        mock_project_repo.get_distinct_clients.return_value = ["Client A"]
        mock_status_repo.get_active_statuses.return_value = [
            _make_status(uuid.uuid4(), "Completed"),
        ]

        result = await filter_service.get_filters()

        assert isinstance(result, FiltersData)
        assert len(result.specializations) == 1
        assert len(result.clients) == 1
        assert len(result.statuses) == 1


class TestGetFiltersEmptyCategories:
    """Tests for FilterService.get_filters when categories are empty."""

    async def test_empty_specializations_returns_empty_array(
        self, filter_service, mock_specialization_repo, mock_project_repo, mock_status_repo
    ):
        """Test that empty specializations returns an empty list."""
        mock_specialization_repo.get_active_specializations.return_value = []
        mock_project_repo.get_distinct_clients.return_value = ["Client A"]
        mock_status_repo.get_active_statuses.return_value = [_make_status(uuid.uuid4(), "Active")]

        result = await filter_service.get_filters()

        assert result.specializations == []

    async def test_empty_clients_returns_empty_array(
        self, filter_service, mock_specialization_repo, mock_project_repo, mock_status_repo
    ):
        """Test that empty clients returns an empty list."""
        mock_specialization_repo.get_active_specializations.return_value = [
            _make_specialization(uuid.uuid4(), "Backend"),
        ]
        mock_project_repo.get_distinct_clients.return_value = []
        mock_status_repo.get_active_statuses.return_value = [_make_status(uuid.uuid4(), "Active")]

        result = await filter_service.get_filters()

        assert result.clients == []

    async def test_empty_statuses_returns_empty_array(
        self, filter_service, mock_specialization_repo, mock_project_repo, mock_status_repo
    ):
        """Test that empty statuses returns an empty list."""
        mock_specialization_repo.get_active_specializations.return_value = [
            _make_specialization(uuid.uuid4(), "Backend"),
        ]
        mock_project_repo.get_distinct_clients.return_value = ["Client A"]
        mock_status_repo.get_active_statuses.return_value = []

        result = await filter_service.get_filters()

        assert result.statuses == []

    async def test_all_categories_empty_returns_all_empty_arrays(
        self, filter_service, mock_specialization_repo, mock_project_repo, mock_status_repo
    ):
        """Test that all empty categories return all empty lists."""
        mock_specialization_repo.get_active_specializations.return_value = []
        mock_project_repo.get_distinct_clients.return_value = []
        mock_status_repo.get_active_statuses.return_value = []

        result = await filter_service.get_filters()

        assert result.specializations == []
        assert result.clients == []
        assert result.statuses == []


class TestClientUuidDeterminism:
    """Tests for deterministic UUID v5 generation for client IDs."""

    async def test_same_client_name_produces_same_uuid(
        self, filter_service, mock_specialization_repo, mock_project_repo, mock_status_repo
    ):
        """Test that the same client name always produces the same UUID v5."""
        mock_specialization_repo.get_active_specializations.return_value = []
        mock_project_repo.get_distinct_clients.return_value = ["Acme Corp"]
        mock_status_repo.get_active_statuses.return_value = []

        result_1 = await filter_service.get_filters()

        # Call again with same data
        mock_project_repo.get_distinct_clients.return_value = ["Acme Corp"]
        result_2 = await filter_service.get_filters()

        assert result_1.clients[0].id == result_2.clients[0].id

    async def test_uuid5_matches_expected_value(
        self, filter_service, mock_specialization_repo, mock_project_repo, mock_status_repo
    ):
        """Test that UUID v5 matches the expected deterministic value from uuid.uuid5."""
        client_name = "Test Client"
        expected_id = str(uuid.uuid5(CLIENT_UUID_NAMESPACE, client_name))

        mock_specialization_repo.get_active_specializations.return_value = []
        mock_project_repo.get_distinct_clients.return_value = [client_name]
        mock_status_repo.get_active_statuses.return_value = []

        result = await filter_service.get_filters()

        assert result.clients[0].id == expected_id

    async def test_different_client_names_produce_different_uuids(
        self, filter_service, mock_specialization_repo, mock_project_repo, mock_status_repo
    ):
        """Test that different client names produce different UUID v5 values."""
        mock_specialization_repo.get_active_specializations.return_value = []
        mock_project_repo.get_distinct_clients.return_value = ["Client A", "Client B"]
        mock_status_repo.get_active_statuses.return_value = []

        result = await filter_service.get_filters()

        assert result.clients[0].id != result.clients[1].id


class TestAlphabeticalSorting:
    """Tests for case-insensitive alphabetical sorting of filter results."""

    async def test_specializations_sorted_case_insensitive(
        self, filter_service, mock_specialization_repo, mock_project_repo, mock_status_repo
    ):
        """Test that specializations are sorted alphabetically (case-insensitive)."""
        mock_specialization_repo.get_active_specializations.return_value = [
            _make_specialization(uuid.uuid4(), "frontend"),
            _make_specialization(uuid.uuid4(), "Backend"),
            _make_specialization(uuid.uuid4(), "DevOps"),
        ]
        mock_project_repo.get_distinct_clients.return_value = []
        mock_status_repo.get_active_statuses.return_value = []

        result = await filter_service.get_filters()

        names = [s.name for s in result.specializations]
        assert names == ["Backend", "DevOps", "frontend"]

    async def test_clients_sorted_case_insensitive(
        self, filter_service, mock_specialization_repo, mock_project_repo, mock_status_repo
    ):
        """Test that clients are sorted alphabetically (case-insensitive)."""
        mock_specialization_repo.get_active_specializations.return_value = []
        mock_project_repo.get_distinct_clients.return_value = ["zebra Corp", "Alpha Inc", "beta LLC"]
        mock_status_repo.get_active_statuses.return_value = []

        result = await filter_service.get_filters()

        names = [c.name for c in result.clients]
        assert names == ["Alpha Inc", "beta LLC", "zebra Corp"]

    async def test_statuses_sorted_case_insensitive(
        self, filter_service, mock_specialization_repo, mock_project_repo, mock_status_repo
    ):
        """Test that statuses are sorted alphabetically (case-insensitive)."""
        mock_specialization_repo.get_active_specializations.return_value = []
        mock_project_repo.get_distinct_clients.return_value = []
        mock_status_repo.get_active_statuses.return_value = [
            _make_status(uuid.uuid4(), "inactive"),
            _make_status(uuid.uuid4(), "Active"),
            _make_status(uuid.uuid4(), "Completed"),
        ]

        result = await filter_service.get_filters()

        names = [s.name for s in result.statuses]
        assert names == ["Active", "Completed", "inactive"]


class TestNullEmptyClientExclusion:
    """Tests verifying that the service handles clean data from the repository.

    The repository is responsible for excluding null/empty client values.
    These tests verify the service correctly processes the clean data it receives.
    """

    async def test_service_handles_clean_client_list(
        self, filter_service, mock_specialization_repo, mock_project_repo, mock_status_repo
    ):
        """Test that service correctly processes a clean list of clients (no nulls/empties)."""
        mock_specialization_repo.get_active_specializations.return_value = []
        mock_project_repo.get_distinct_clients.return_value = ["Valid Client"]
        mock_status_repo.get_active_statuses.return_value = []

        result = await filter_service.get_filters()

        assert len(result.clients) == 1
        assert result.clients[0].name == "Valid Client"

    async def test_repository_called_for_distinct_clients(
        self, filter_service, mock_specialization_repo, mock_project_repo, mock_status_repo
    ):
        """Test that the project repository's get_distinct_clients is called."""
        mock_specialization_repo.get_active_specializations.return_value = []
        mock_project_repo.get_distinct_clients.return_value = []
        mock_status_repo.get_active_statuses.return_value = []

        await filter_service.get_filters()

        mock_project_repo.get_distinct_clients.assert_awaited_once()
