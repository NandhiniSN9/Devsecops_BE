"""Report generation route for email notification service.

Provides the endpoint triggered by the external cron job:
- GET /reports/generate — Generate and email reports for all active specializations

No authentication required — triggered by external cron.
No request body required.
"""

import asyncio
import traceback

from fastapi import APIRouter, Depends
from src.models.response.base_response import BaseResponse
from src.services.dependencies import get_report_service
from src.services.report_service import ReportService
from src.utils.logger import logger

router = APIRouter(prefix="/reports")


@router.get("/generate")
async def generate_reports(
    report_service: ReportService = Depends(get_report_service),
) -> BaseResponse:
    """Trigger report generation for all active specializations.
    This endpoint is called by an external daily cron job with no request body.
    It internally iterates over all active specializations, evaluates frequency
    settings, generates PDF reports, uploads to S3, and sends emails via
    Microsoft Graph API.

    No authentication required — the cron simply triggers the endpoint.

    Args:
        report_service: Injected ReportService instance.

    Returns:
        BaseResponse with success status.
    """
    try:
        logger.info("Report generation endpoint triggered by cron")

        await report_service.generate_reports()

        return BaseResponse(
            status_code=200,
            status="success",
            message="Email sent successfully",
            data=[],
        )
    except Exception as exc:
        logger.error("Error in generate_reports endpoint", error=str(exc))
        asyncio.create_task(log_error_to_db(
            error_message=str(exc),
            error_function="generate_reports",
            error_file="src/routes/report_route.py",
            stack_trace=traceback.format_exc(),
            created_by="system",
        ))
        raise
