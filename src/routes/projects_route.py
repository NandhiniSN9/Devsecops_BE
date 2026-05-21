"""Projects route for listing projects and performing project actions."""

import asyncio
import traceback

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile

from src.models.request.projects_request import ProjectActionEnum
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
    project_id: str = Form(...),
    project_name: str = Form(...),
    action: str = Form(...),
    reason_category: str | None = Form(default=None),
    comments: str | None = Form(default=None),
    evidence_url: UploadFile | None = File(default=None),
    projects_service: ProjectsService = Depends(get_projects_service),
) -> BaseResponse:
    """Perform an action on a project (mark_not_applicable or mark_complete).

    Accepts multipart/form-data with project_id, project_name, action, and
    optional reason_category, comments, and evidence_url fields.

    Args:
        request: The incoming request (for extracting user context).
        project_id: UUID of the project.
        project_name: Human-readable name of the project.
        action: Action to perform — mark_complete or mark_not_applicable.
        reason_category: Required when action is mark_not_applicable.
        comments: Required when action is mark_not_applicable.
        evidence_url: Optional evidence file upload (mark_not_applicable only).
        projects_service: Injected ProjectsService instance.

    Returns:
        BaseResponse with project_id, project_name, and optional evidence_url.
    """
    # Validate required fields for mark_not_applicable at the route level
    if action == ProjectActionEnum.MARK_NOT_APPLICABLE:
        if not reason_category or not reason_category.strip():
            raise HTTPException(status_code=422, detail="reason_category is required for mark_not_applicable action")
        if not comments or not comments.strip():
            raise HTTPException(status_code=422, detail="comments is required for mark_not_applicable action")

    # Extract user identifier from request state (set by auth middleware)
    user_id = getattr(request.state, "user_id", None) or getattr(request.state, "email", "system")

    try:
        return await projects_service.perform_action(
            project_id=project_id,
            project_name=project_name,
            action=action,
            reason_category=reason_category,
            comments=comments,
            evidence_file=evidence_url,
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
