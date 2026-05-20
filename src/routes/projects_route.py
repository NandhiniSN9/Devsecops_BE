"""Projects route for listing projects and performing project actions."""

import asyncio
import traceback

from fastapi import APIRouter, Depends, Query, Request

from src.models.request.projects_request import ProjectActionRequest
from src.models.response.base_response import BaseResponse
from src.services.dependencies import get_projects_service
from src.services.projects_service import ProjectsService
from src.utils.logger import logger

router = APIRouter(prefix="")


@router.get("/projects")
async def get_projects(
    period: str | None = Query(default=None),
    search: str | None = Query(default=None),  # Project name only. Case insensitive and partial search allowed.
    status: str | None = Query(default=None),
    client: str | None = Query(default=None),
    specialization: str | None = Query(default=None),
    min_overdue_days: int | None = Query(default=None),
    offset: int = Query(default=0),
    limit: int = Query(default=10),
    sort_by: str | None = Query(default=None),
    sort_order: str | None = Query(default=None),
    projects_service: ProjectsService = Depends(get_projects_service),
) -> BaseResponse:
    """Retrieve paginated list of projects with filtering and sorting.

    Args:
        period: Time period filter (all, last_week, last_month, last_3_months, last_6_months, last_year).
        search: Free text search on project name.
        status: Comma-separated status IDs to filter by.
        client: Comma-separated client IDs to filter by.
        specialization: Comma-separated specialization IDs to filter by.
        min_overdue_days: Minimum overdue days filter — only return projects with overdue_days >= this value.
        offset: Number of items to skip for pagination.
        limit: Number of items per page (1-100).
        sort_by: Field to sort by (project, onboarded_date).
        sort_order: Sort direction (asc, desc).
        projects_service: Injected ProjectsService instance.

    Returns:
        BaseResponse with projects list and pagination metadata.
    """
    try:
        return await projects_service.get_projects(
            period=period,
            search=search,
            status=status,
            client=client,
            specialization=specialization,
            min_overdue_days=min_overdue_days,
            offset=offset,
            limit=limit,
            sort_by=sort_by,
            sort_order=sort_order,
        )
    except Exception as exc:
        logger.error("Error in get_projects endpoint", error=str(exc))
        asyncio.create_task(log_error_to_db(
            error_message=str(exc),
            error_function="get_projects",
            error_file="src/routes/projects_route.py",
            stack_trace=traceback.format_exc(),
            created_by="system",
        ))
        raise


@router.post("/projects/action")
async def perform_project_action(
    request: Request,
    body: ProjectActionRequest,
    projects_service: ProjectsService = Depends(get_projects_service),
) -> BaseResponse:
    """Perform an action on a project (mark_not_applicable or mark_complete).

    Accepts a JSON body with project_id, project_name, action, and optional
    reason_category, comments, and evidence_url fields.

    Args:
        request: The incoming request (for extracting user context).
        body: JSON request body with action details.
        projects_service: Injected ProjectsService instance.

    Returns:
        BaseResponse with project_id, project_name, and optional evidence_url.
    """
    # Extract user identifier from request state (set by auth middleware)
    user_id = getattr(request.state, "user_id", None) or getattr(request.state, "email", "system")

    try:
        return await projects_service.perform_action(
            project_id=body.project_id,
            project_name=body.project_name,
            action=body.action,
            reason_category=body.reason_category,
            comments=body.comments,
            evidence_file=None,
            user_id=user_id,
        )
    except Exception as exc:
        logger.error("Error in perform_project_action endpoint", error=str(exc))
        asyncio.create_task(log_error_to_db(
            error_message=str(exc),
            error_function="perform_project_action",
            error_file="src/routes/projects_route.py",
            stack_trace=traceback.format_exc(),
            created_by="system",
        ))
        raise
