"""ADO sync route for triggering Azure DevOps data synchronization."""

from fastapi import APIRouter, BackgroundTasks, Depends

from src.models.response.base_response import BaseResponse
from src.services.ado_sync_service import AdoSyncService
from src.services.dependencies import get_ado_sync_service

router = APIRouter(prefix="")


@router.get("/sync/ado")
async def sync_ado(
    background_tasks: BackgroundTasks,
    service: AdoSyncService = Depends(get_ado_sync_service),
) -> BaseResponse:
    """Trigger Azure DevOps data synchronization.

    Args:
        background_tasks: FastAPI background tasks runner.
        service: Injected AdoSyncService instance.

    Returns:
        BaseResponse with success message or conflict error.
    """
    result = await service.initiate_sync()

    if not result["success"]:
        return BaseResponse(
            status_code=409,
            status="failed",
            message=result["message"],
            data=None,
        )

    background_tasks.add_task(service.run_sync, result["cron_id"])

    return BaseResponse(
        status_code=200,
        status="success",
        message=result["message"],
        data=None,
    )
