"""Projects route for listing projects and performing project actions."""

from fastapi import APIRouter, Depends, Form, Query, Request, UploadFile
from fastapi.params import File

from src.dtos.response.base_response import BaseResponse
from src.services.dependencies import get_projects_service
from src.services.projects_service import ProjectsService

router = APIRouter(prefix="")


@router.get("/projects")
async def get_projects(
    period: str | None = Query(default=None),
    search: str | None = Query(default=None),
    status: str | None = Query(default=None),
    client: str | None = Query(default=None),
    specialization: str | None = Query(default=None),
    offset: int = Query(default=0),
    limit: int = Query(default=10),
    sort_by: str | None = Query(default=None),
    sort_order: str | None = Query(default=None),
    projects_service: ProjectsService = Depends(get_projects_service),
) -> BaseResponse:
    """Retrieve paginated list of projects with filtering and sorting.

    Args:
        period: Time period filter (last_week, last_month, last_3_months, last_6_months, last_year).
        search: Free text search on project name.
        status: Comma-separated status IDs to filter by.
        client: Comma-separated client IDs to filter by.
        specialization: Comma-separated specialization IDs to filter by.
        offset: Number of items to skip for pagination.
        limit: Number of items per page (1-100).
        sort_by: Field to sort by (project, onboarded_date).
        sort_order: Sort direction (asc, desc).
        projects_service: Injected ProjectsService instance.

    Returns:
        BaseResponse with projects list and pagination metadata.
    """
    return await projects_service.get_projects(
        period=period,
        search=search,
        status=status,
        client=client,
        specialization=specialization,
        offset=offset,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.post("/projects/action")
async def perform_project_action(
    request: Request,
    project_id: str = Form(...),
    action: str = Form(...),
    reason_category: str | None = Form(default=None),
    comments: str | None = Form(default=None),
    evidence_file: UploadFile | None = File(default=None),
    projects_service: ProjectsService = Depends(get_projects_service),
) -> BaseResponse:
    """Perform an action on a project (mark_not_applicable or mark_complete).

    Args:
        request: The incoming request (for extracting user context).
        project_id: UUID of the project.
        action: Action to perform (mark_not_applicable, mark_complete).
        reason_category: Reason category (required for mark_not_applicable).
        comments: Comments (required for mark_not_applicable).
        evidence_file: Optional evidence file attachment.
        projects_service: Injected ProjectsService instance.

    Returns:
        BaseResponse with success message.
    """
    # Extract user identifier from request state (set by auth middleware)
    user_id = getattr(request.state, "user_id", "system")

    return await projects_service.perform_action(
        project_id=project_id,
        action=action,
        reason_category=reason_category,
        comments=comments,
        evidence_file=evidence_file,
        user_id=user_id,
    )
