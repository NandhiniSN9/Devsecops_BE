"""Report generation route for email notification service.

Provides the endpoint triggered by the external cron job:
- POST /reports/generate — Generate and email reports for all active specializations
- POST /reports/test-email — Send a test email to verify Graph API connectivity

No authentication required — triggered by external cron.
No request body required.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr

from src.client.graph_client import GraphClient
from src.dtos.response.base_response import BaseResponse
from src.services.dependencies import get_graph_client, get_report_service
from src.services.report_service import ReportService
from src.utils.logger import logger

router = APIRouter(prefix="/reports")


class TestEmailRequest(BaseModel):
    """Request body for the test email endpoint."""

    to_email: EmailStr
    subject: str = "[DevSecOps Dashboard] Test Email"
    message: str = "This is a test email from the DevSecOps Dashboard backend."


@router.post("/test-email")
async def send_test_email(
    request: TestEmailRequest,
    graph_client: GraphClient = Depends(get_graph_client),
) -> BaseResponse:
    """Send a simple test email to verify Microsoft Graph API connectivity.

    This endpoint bypasses PDF generation and S3 — it just sends a plain HTML email.

    Args:
        request: Email recipient and optional subject/message.
        graph_client: Injected GraphClient instance.

    Returns:
        BaseResponse with success or failure status.
    """
    logger.info("Test email endpoint triggered", to=request.to_email)

    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px;">
        <h2>DevSecOps Dashboard — Test Email</h2>
        <p>{request.message}</p>
        <hr style="border: none; border-top: 1px solid #eee; margin-top: 20px;">
        <p style="color: #999; font-size: 11px;">
            This is an automated test email from the DevSecOps Dashboard.
        </p>
    </body>
    </html>
    """

    sent = await graph_client.send_email(
        to_email=request.to_email,
        subject=request.subject,
        html_body=html_body,
    )

    if sent:
        return BaseResponse(
            status_code=200,
            status="success",
            message=f"Test email sent successfully to {request.to_email}",
            data=[],
        )
    else:
        return BaseResponse(
            status_code=500,
            status="error",
            message="Failed to send test email. Check Graph API credentials and permissions.",
            data=[],
        )


@router.post("/generate")
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
    logger.info("Report generation endpoint triggered by cron")

    await report_service.generate_reports()

    return BaseResponse(
        status_code=200,
        status="success",
        message="Email sent successfully",
        data=[],
    )
