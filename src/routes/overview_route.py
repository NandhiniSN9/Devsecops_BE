"""Overview route for retrieving consolidated KPI metrics and status distribution."""

from fastapi import APIRouter, Depends, Query

from src.models.response.base_response import BaseResponse
from src.services.dependencies import get_overview_service
from src.services.overview_service import OverviewService
from src.utils.logger import logger

router = APIRouter(prefix="")


@router.get("/overview")
async def get_overview(
    period: str | None = Query(default=None),
    specialization: str | None = Query(default=None),
    overview_service: OverviewService = Depends(get_overview_service),
) -> BaseResponse:
    """Retrieve consolidated overview dashboard data.

    Args:
        period: Period filter (last_week, last_month, last_3_months). Defaults to last_week.
        specialization: Comma-separated specialization IDs to filter by. Empty means all.
        overview_service: Injected OverviewService instance.

    Returns:
        BaseResponse with overview metrics and status distribution.
    """
    try:
        overview_data = await overview_service.get_overview(period, specialization)

        return BaseResponse(
            status_code=200,
            status="success",
            message="Overview data retrieved successfully",
            data=overview_data.model_dump(),
        )
    except Exception as exc:
        logger.error("Error in get_overview endpoint", error=str(exc))
        raise
