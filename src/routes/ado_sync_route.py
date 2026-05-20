"""ADO sync route for triggering Azure DevOps data synchronization."""

import asyncio
import traceback

from fastapi import APIRouter, BackgroundTasks, Depends

from src.models.response.base_response import BaseResponse
from src.services.ado_sync_service import AdoSyncService
from src.services.dependencies import get_ado_sync_service
from src.utils.logger import logger

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
    try:
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
    except Exception as exc:
        logger.error("Error in sync_ado endpoint", error=str(exc))
        asyncio.create_task(log_error_to_db(
            error_message=str(exc),
            error_function="sync_ado",
            error_file="src/routes/ado_sync_route.py",
            stack_trace=traceback.format_exc(),
            created_by="system",
        ))
        raise
