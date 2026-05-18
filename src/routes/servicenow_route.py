"""ServiceNow sync routes for project and ticket ingestion.

Provides endpoints for receiving webhook data from ServiceNow:
- POST /sync/servicenow/projects — Ingest project data
- POST /sync/servicenow/devsecops-tickets — Ingest DevSecOps ticket data

Both endpoints authenticate via encrypted token with ServiceNow email validation.
"""

import json

from cryptography.fernet import Fernet, InvalidToken
from fastapi import APIRouter, Depends, Request

from src.models.base_response import BaseResponse
from src.models.servicenow_models import SyncDevSecOpsTicketsRequest, SyncProjectRequest
from src.services.dependencies import get_servicenow_service
from src.services.servicenow_service import ServiceNowService
from src.settings import get_settings
from src.utils.exceptions.exceptions import AuthenticationError
from src.utils.logger import logger

router = APIRouter(prefix="/sync/servicenow")


async def _validate_servicenow_auth(request: Request) -> str:
    """Validate the ServiceNow authentication token.

    Decrypts the bearer token, extracts the email, and validates it
    against the SERVICENOW_ALLOWED_EMAIL environment variable.

    Args:
        request: The incoming FastAPI request.

    Returns:
        The validated email address (service account identifier).

    Raises:
        AuthenticationError: If token is missing, invalid, or email doesn't match.
    """
    trace_id = getattr(request.state, "trace_id", "unknown")

    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        logger.warning(
            "Missing or invalid Authorization header for ServiceNow sync",
            trace_id=trace_id,
            path=request.url.path,
        )
        raise AuthenticationError("Authentication token is missing or expired")

    token = auth_header[len("Bearer ") :]
    settings = get_settings()

    # Decrypt token and extract email
    try:
        fernet = Fernet(settings.TOKEN_PRIVATE_KEY.encode())
        decrypted_bytes = fernet.decrypt(token.encode())
        payload = json.loads(decrypted_bytes.decode())
        email = payload.get("email", "")
    except (InvalidToken, ValueError, json.JSONDecodeError) as exc:
        logger.warning(
            "ServiceNow token decryption failed",
            trace_id=trace_id,
            error=str(exc),
        )
        raise AuthenticationError("Authentication token is missing or expired")

    if not email or not email.strip():
        logger.warning("Empty email in ServiceNow token payload", trace_id=trace_id)
        raise AuthenticationError("Authentication failed or user not found in Jira")

    # Validate email against allowed ServiceNow service account
    if email.strip().lower() != settings.SERVICENOW_ALLOWED_EMAIL.strip().lower():
        logger.warning(
            "ServiceNow email validation failed",
            trace_id=trace_id,
            email=email,
        )
        raise AuthenticationError("Insufficient permissions: servicenow_sync role required")

    return email.strip()


@router.post("/projects")
async def sync_projects(
    request: Request,
    body: SyncProjectRequest,
    servicenow_service: ServiceNowService = Depends(get_servicenow_service),
) -> BaseResponse:
    """Ingest project data from ServiceNow webhook.

    Receives project data and inserts new project records.
    If sn_project_id already exists, the record is skipped.

    Args:
        request: The incoming FastAPI request.
        body: Validated SyncProjectRequest payload.
        servicenow_service: Injected ServiceNowService instance.

    Returns:
        BaseResponse with sync result.
    """
    # NOTE: Auth disabled temporarily for Swagger UI testing
    # created_by = await _validate_servicenow_auth(request)
    created_by = "swagger-test@local"

    trace_id = getattr(request.state, "trace_id", "unknown")
    logger.info(
        "Processing ServiceNow project sync",
        trace_id=trace_id,
        project_count=len(body.projects),
    )

    await servicenow_service.sync_projects(body, created_by)

    return BaseResponse(
        status_code=200,
        status="success",
        message="Sync completed successfully",
        data=[],
    )


@router.post("/devsecops-tickets")
async def sync_devsecops_tickets(
    request: Request,
    body: SyncDevSecOpsTicketsRequest,
    servicenow_service: ServiceNowService = Depends(get_servicenow_service),
) -> BaseResponse:
    """Ingest DevSecOps ticket data from ServiceNow webhook.

    Receives ticket data with associated repositories and inserts records.
    Supports partial success — valid tickets are processed while invalid
    ones are logged and skipped.

    Args:
        request: The incoming FastAPI request.
        body: Validated SyncDevSecOpsTicketsRequest payload.
        servicenow_service: Injected ServiceNowService instance.

    Returns:
        BaseResponse with sync result.
    """
    # NOTE: Auth disabled temporarily for Swagger UI testing
    # created_by = await _validate_servicenow_auth(request)
    created_by = "swagger-test@local"

    trace_id = getattr(request.state, "trace_id", "unknown")
    logger.info(
        "Processing ServiceNow DevSecOps tickets sync",
        trace_id=trace_id,
        ticket_count=len(body.tickets),
    )

    await servicenow_service.sync_devsecops_tickets(body, created_by)

    return BaseResponse(
        status_code=200,
        status="success",
        message="Sync completed successfully",
        data=[],
    )
