"""ADO sync route for triggering Azure DevOps data synchronization."""

from fastapi import APIRouter, Depends

from src.dtos.request.ado_sync_request import AdoSyncRequest
from src.dtos.response.base_response import BaseResponse
from src.services.ado_sync_service import AdoSyncService
from src.services.dependencies import get_ado_sync_service

router = APIRouter(prefix="")


@router.post("/sync/ado")
async def sync_ado(
    request: AdoSyncRequest = AdoSyncRequest(),
    service: AdoSyncService = Depends(get_ado_sync_service),
) -> BaseResponse:
    """Trigger Azure DevOps data synchronization.

    Args:
        request: Optional request body with specialization_id filter.
        service: Injected AdoSyncService instance.

    Returns:
        BaseResponse with success message.
    """
    message = await service.sync_ado_data(specialization_id=request.specialization_id)

    return BaseResponse(
        status_code=200,
        status="success",
        message=message,
        data=None,
    )
