"""
Filter route for retrieving dropdown filter options.
"""

import asyncio
import traceback

from fastapi import APIRouter, Depends, Response
from src.models.response.base_response import BaseResponse
from src.services.dependencies import get_filter_service
from src.services.filter_service import FilterService
from src.settings import FILTER_CACHE_MAX_AGE
from src.utils.logger import logger

router = APIRouter(prefix="")


@router.get("/filters")
async def get_filters(response: Response,filter_service: FilterService = Depends(get_filter_service)) -> BaseResponse:
    """Retrieve all available filter options for dashboard dropdowns.

    Returns specializations, clients, and statuses arrays sorted alphabetically.
    Sets Cache-Control header with max-age of 3600 seconds.

    Args:
        response: FastAPI Response object for setting headers.
        filter_service: Injected FilterService instance.

    Returns:
        BaseResponse with filters data containing specializations, clients, and statuses.
    """
    try:
        filters_data = await filter_service.get_filters()

        response.headers["Cache-Control"] = f"max-age={FILTER_CACHE_MAX_AGE}"

        return BaseResponse(
            status_code=200,
            status="success",
            message="Filters retrieved successfully",
            data=filters_data.model_dump(),
        )
    except Exception as exc:
        logger.error("Error in get_filters endpoint", error=str(exc))
        asyncio.create_task(log_error_to_db(
            error_message=str(exc),
            error_function="get_filters",
            error_file="src/routes/filter_route.py",
            stack_trace=traceback.format_exc(),
            created_by="system",
        ))
        raise
