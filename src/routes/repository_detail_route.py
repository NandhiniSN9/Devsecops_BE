"""Repository detail route for retrieving comprehensive repository information."""

from fastapi import APIRouter, Depends

from src.dtos.response.base_response import BaseResponse
from src.services.dependencies import get_repository_detail_service
from src.services.repository_detail_service import RepositoryDetailService

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
    detail = await service.get_repository_detail(repository_id)

    return BaseResponse(
        status_code=200,
        status="success",
        message="Repository detail retrieved successfully",
        data=detail.model_dump(),
    )
