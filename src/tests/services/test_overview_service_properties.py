"""Property-based tests for OverviewService period default behavior.

**Validates: Requirements 1.2**
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.models.query_params import PeriodEnum
from src.repositories.kpi_history_repository import KpiHistoryRepository
from src.repositories.project_repository import ProjectRepository
from src.repositories.specialization_repository import SpecializationRepository
from src.services.overview_service import OverviewService


@given(st.just(None))
@settings(max_examples=50)
def test_validate_period_none_always_returns_last_week(period: None) -> None:
    """**Validates: Requirements 1.2**

    Property 2: Period Default Behavior
    When period is None, _validate_period always returns "last_week".
    """
    kpi_repo = MagicMock(spec=KpiHistoryRepository)
    project_repo = MagicMock(spec=ProjectRepository)
    specialization_repo = MagicMock(spec=SpecializationRepository)

    service = OverviewService(
        kpi_repo=kpi_repo,
        project_repo=project_repo,
        specialization_repo=specialization_repo,
    )

    result = service._validate_period(period)
    assert result == PeriodEnum.LAST_WEEK.value
    assert result == "last_week"


@pytest.mark.asyncio
@given(st.just(None))
@settings(max_examples=50)
async def test_get_overview_with_none_period_uses_7_days(period: None) -> None:
    """**Validates: Requirements 1.2**

    Property 2: Period Default Behavior
    When period is None, get_overview calls kpi_repo.get_latest_by_specializations with period_days=7.
    """
    kpi_repo = AsyncMock(spec=KpiHistoryRepository)
    project_repo = AsyncMock(spec=ProjectRepository)
    specialization_repo = AsyncMock(spec=SpecializationRepository)

    # Mock return values
    kpi_repo.get_latest_by_specializations.return_value = []
    project_repo.get_status_distribution.return_value = []

    service = OverviewService(
        kpi_repo=kpi_repo,
        project_repo=project_repo,
        specialization_repo=specialization_repo,
    )

    await service.get_overview(period=period, specialization=None)

    # Verify that kpi_repo was called with period_days=7 (last_week default)
    kpi_repo.get_latest_by_specializations.assert_called_once_with(None, 7)
