"""Repository detail route for retrieving comprehensive repository information."""

import asyncio
import traceback

from fastapi import APIRouter, Depends

from src.models.response.base_response import BaseResponse
from src.services.dependencies import get_repository_detail_service
from src.services.repository_detail_service import RepositoryDetailService
from src.utils.exceptions.exceptions import InvalidParameterError, NotFoundError
from src.utils.logger import logger

router = APIRouter(prefix="")


@router.get("/repositories/{repository_id}")
async def get_repository_detail(
    repository_id: str,
    service: RepositoryDetailService = Depends(get_repository_detail_service),
) -> BaseResponse:
    """Retrieve comprehensive detail for a repository.

    Args:
        repository_id: UUID of the repository (path parameter).
        service: Injected RepositoryDetailService instance.

    Returns:
        BaseResponse with repository detail data.
    """
    try:
        detail = await service.get_repository_detail(repository_id)

        return BaseResponse(
            status_code=200,
            status="success",
            message="Repository detail retrieved successfully",
            data=detail.model_dump(),
        )
    except (InvalidParameterError, NotFoundError):
        raise
    except Exception as exc:
        logger.error("Error in get_repository_detail endpoint", error=str(exc))
        asyncio.create_task(log_error_to_db(
            error_message=str(exc),
            error_function="get_repository_detail",
            error_file="src/routes/repository_detail_route.py",
            stack_trace=traceback.format_exc(),
            created_by="system",
        ))
        raise
