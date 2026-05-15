"""Property-based tests for OverviewService period default behavior.

**Validates: Requirements 1.2**
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.models.query_params import PeriodEnum
from src.repositories.overview_repository import OverviewRepository
from src.services.overview_service import OverviewService


@given(st.just(None))
@settings(max_examples=50)
def test_validate_period_none_always_returns_last_week(period: None) -> None:
    """**Validates: Requirements 1.2**

    Property 2: Period Default Behavior
    When period is None, _validate_period always returns "last_week".
    """
    overview_repo = MagicMock(spec=OverviewRepository)

    service = OverviewService(
        overview_repo=overview_repo,
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
    When period is None, get_overview calls repo.get_latest_by_specializations with period_days=7.
    """
    overview_repo = AsyncMock(spec=OverviewRepository)

    # Mock return values
    overview_repo.get_latest_by_specializations.return_value = []
    overview_repo.get_status_distribution.return_value = []

    service = OverviewService(
        overview_repo=overview_repo,
    )

    await service.get_overview(period=period, specialization=None)

    # Verify that repo was called with period_days=7 (last_week default)
    overview_repo.get_latest_by_specializations.assert_called_once_with(None, 7)
