"""Projects service for listing projects and performing project actions."""

import uuid
from datetime import datetime

from fastapi import UploadFile

from src.client.s3_client import S3Client
from src.dtos.request.projects_request import (
    ProjectActionEnum,
    ProjectPeriodEnum,
    ProjectSortByEnum,
    ProjectSortOrderEnum,
)
from src.dtos.response.base_response import BaseResponse
from src.dtos.response.projects_response import (
    PaginationResponse,
    ProjectItemResponse,
    ProjectsListDataResponse,
    RepositoryItemResponse,
)
from src.repositories.projects_repository import ProjectsRepository
from src.settings import PROJECTS_PERIOD_DAYS_MAP
from src.utils.exceptions import InvalidParameterError, NotFoundError


class ProjectsService:
    """Service for projects listing and action operations."""

    def __init__(
        self,
        projects_repo: ProjectsRepository,
        s3_client: S3Client,
    ) -> None:
        """Initialize with repository and S3 client dependencies."""
        self._projects_repo = projects_repo
        self._s3_client = s3_client

    async def get_projects(
        self,
        period: str | None,
        search: str | None,
        status: str | None,
        client: str | None,
        specialization: str | None,
        offset: int,
        limit: int,
        sort_by: str | None,
        sort_order: str | None,
    ) -> BaseResponse:
        """Retrieve paginated list of projects with filtering and sorting.

        Args:
            period: Time period filter.
            search: Free text search on project name.
            status: Comma-separated status IDs.
            client: Comma-separated client IDs.
            specialization: Comma-separated specialization IDs.
            offset: Pagination offset.
            limit: Pagination limit.
            sort_by: Sort field.
            sort_order: Sort direction.

        Returns:
            BaseResponse with projects list and pagination metadata.

        Raises:
            InvalidParameterError: If any parameter is invalid.
        """
        # Validate parameters
        validated_period = self._validate_period(period)
        validated_sort_by = self._validate_sort_by(sort_by)
        validated_sort_order = self._validate_sort_order(sort_order)
        self._validate_offset(offset)
        self._validate_limit(limit)

        period_days = PROJECTS_PERIOD_DAYS_MAP[validated_period]

        # Parse filter values
        status_ids = self._parse_uuid_csv(status)
        client_ids = self._parse_csv(client)
        specialization_ids = self._parse_uuid_csv(specialization)

        # Fetch projects from repository
        projects, total_items = await self._projects_repo.get_projects(
            period_days=period_days,
            search=search,
            status_ids=status_ids,
            client_ids=client_ids,
            specialization_ids=specialization_ids,
            offset=offset,
            limit=limit,
            sort_by=validated_sort_by,
            sort_order=validated_sort_order,
        )

        # Build response items with nested repositories
        project_items: list[ProjectItemResponse] = []
        for project in projects:
            repositories = await self._projects_repo.get_repositories_for_project(project.project_id)
            status_name = await self._projects_repo.get_status_name_for_project(project)

            repo_items = [
                RepositoryItemResponse(
                    id=repo.repository_id,
                    name=repo.repository_name,
                    onboarded_date=repo.created_at.date() if repo.created_at else None,
                    status=self._determine_repo_status(repo),
                )
                for repo in repositories
            ]

            at_risk_overdue = self._calculate_at_risk_overdue(project, repo_items)

            project_items.append(
                ProjectItemResponse(
                    id=project.project_id,
                    name=project.project_name,
                    onboarded_date=project.onboarded_date,
                    repository_count=len(repo_items),
                    status=status_name or "Unknown",
                    overdue_days=at_risk_overdue,
                    repositories=repo_items,
                )
            )

        data = ProjectsListDataResponse(
            projects=project_items,
            pagination=PaginationResponse(
                offset=offset,
                limit=limit,
                total_items=total_items,
            ),
        )

        return BaseResponse(
            status_code=200,
            status="success",
            message="Projects retrieved successfully",
            data=data.model_dump(),
        )

    async def perform_action(
        self,
        project_id: str,
        action: str,
        reason_category: str | None,
        comments: str | None,
        evidence_file: UploadFile | None,
        user_id: str,
    ) -> BaseResponse:
        """Perform an action on a project (mark not applicable or mark complete).

        Args:
            project_id: UUID string of the project.
            action: Action to perform.
            reason_category: Reason category (required for mark_not_applicable).
            comments: Comments (required for mark_not_applicable).
            evidence_file: Optional evidence file upload.
            user_id: Authenticated user identifier.

        Returns:
            BaseResponse with success message.

        Raises:
            InvalidParameterError: If validation fails.
            NotFoundError: If project not found.
        """
        # Validate project_id
        parsed_project_id = self._validate_project_id(project_id)

        # Validate action
        self._validate_action(action)

        # Check project exists
        project = await self._projects_repo.get_project_by_id(parsed_project_id)
        if project is None:
            raise NotFoundError("Project not found")

        if action == ProjectActionEnum.MARK_NOT_APPLICABLE:
            await self._mark_not_applicable(
                parsed_project_id, reason_category, comments, evidence_file, user_id
            )
        elif action == ProjectActionEnum.MARK_COMPLETE:
            await self._mark_complete(parsed_project_id, user_id)

        return BaseResponse(
            status_code=200,
            status="success",
            message="Action performed successfully",
            data=None,
        )

    async def _mark_not_applicable(
        self,
        project_id: uuid.UUID,
        reason_category: str | None,
        comments: str | None,
        evidence_file: UploadFile | None,
        user_id: str,
    ) -> None:
        """Handle mark_not_applicable action logic.

        Args:
            project_id: The project UUID.
            reason_category: Required reason category.
            comments: Required comments.
            evidence_file: Optional evidence file.
            user_id: Authenticated user identifier.

        Raises:
            InvalidParameterError: If required fields are missing.
        """
        if not reason_category:
            raise InvalidParameterError(
                "reason_category is required for mark_not_applicable action"
            )
        if not comments:
            raise InvalidParameterError(
                "comments is required for mark_not_applicable action"
            )

        # Look up Not Applicable status
        status = await self._projects_repo.get_status_by_name("Not Applicable")
        if status is None:
            raise InvalidParameterError("Status 'Not Applicable' not found in system")

        # Upload evidence file if provided
        evidence_url: str | None = None
        if evidence_file and evidence_file.filename:
            evidence_url = await self._upload_evidence(evidence_file, project_id)

        try:
            # Update project
            await self._projects_repo.update_project_not_applicable(
                project_id=project_id,
                status_id=status.status_id,
                modified_by=user_id,
            )

            # Create Jira ticket record
            jira_id = f"ZDAD-NA-{int(datetime.utcnow().timestamp())}"
            await self._projects_repo.create_jira_ticket(
                project_id=project_id,
                jira_id=jira_id,
                reason_category=reason_category,
                comments=comments,
                evidence_url=evidence_url,
                created_by=user_id,
            )

            await self._projects_repo.commit()
        except Exception:
            await self._projects_repo.rollback()
            raise

    async def _mark_complete(
        self,
        project_id: uuid.UUID,
        user_id: str,
    ) -> None:
        """Handle mark_complete action logic.

        Args:
            project_id: The project UUID.
            user_id: Authenticated user identifier.
        """
        # Look up Completed status
        status = await self._projects_repo.get_status_by_name("Completed")
        if status is None:
            raise InvalidParameterError("Status 'Completed' not found in system")

        try:
            await self._projects_repo.update_project_complete(
                project_id=project_id,
                status_id=status.status_id,
                modified_by=user_id,
            )
            await self._projects_repo.commit()
        except Exception:
            await self._projects_repo.rollback()
            raise

    async def _upload_evidence(self, file: UploadFile, project_id: uuid.UUID) -> str:
        """Upload evidence file to S3.

        Args:
            file: The uploaded file.
            project_id: The project UUID for key generation.

        Returns:
            The S3 URL of the uploaded file.
        """
        timestamp = int(datetime.utcnow().timestamp())
        s3_key = f"evidence/{project_id}/{timestamp}_{file.filename}"
        file_bytes = await file.read()
        await self._s3_client.upload_pdf(file_bytes, s3_key)
        presigned_url = await self._s3_client.generate_presigned_url(s3_key)
        return presigned_url

    @staticmethod
    def _validate_period(period: str | None) -> str:
        """Validate period parameter."""
        if period is None:
            return ProjectPeriodEnum.LAST_MONTH.value

        valid_values = [e.value for e in ProjectPeriodEnum]
        if period not in valid_values:
            raise InvalidParameterError(
                f"Invalid query parameter: 'period' must be one of {valid_values}"
            )
        return period

    @staticmethod
    def _validate_sort_by(sort_by: str | None) -> str:
        """Validate sort_by parameter."""
        if sort_by is None:
            return ProjectSortByEnum.PROJECT.value

        valid_values = [e.value for e in ProjectSortByEnum]
        if sort_by not in valid_values:
            raise InvalidParameterError(
                f"Invalid query parameter: 'sort_by' must be one of {valid_values}"
            )
        return sort_by

    @staticmethod
    def _validate_sort_order(sort_order: str | None) -> str:
        """Validate sort_order parameter."""
        if sort_order is None:
            return ProjectSortOrderEnum.ASC.value

        valid_values = [e.value for e in ProjectSortOrderEnum]
        if sort_order not in valid_values:
            raise InvalidParameterError(
                f"Invalid query parameter: 'sort_order' must be one of {valid_values}"
            )
        return sort_order

    @staticmethod
    def _validate_offset(offset: int) -> None:
        """Validate offset parameter."""
        if offset < 0:
            raise InvalidParameterError(
                "Invalid query parameter: 'offset' must be a non-negative integer"
            )

    @staticmethod
    def _validate_limit(limit: int) -> None:
        """Validate limit parameter."""
        if limit < 1 or limit > 100:
            raise InvalidParameterError(
                "Invalid query parameter: 'limit' must be between 1 and 100"
            )

    @staticmethod
    def _validate_project_id(project_id: str) -> uuid.UUID:
        """Validate and parse project_id as UUID."""
        if not project_id:
            raise InvalidParameterError(
                "project_id is required and must be a valid UUID"
            )
        try:
            return uuid.UUID(project_id)
        except (ValueError, AttributeError):
            raise InvalidParameterError(
                "project_id is required and must be a valid UUID"
            )

    @staticmethod
    def _validate_action(action: str) -> None:
        """Validate action parameter."""
        if not action:
            raise InvalidParameterError(
                "action must be one of [mark_not_applicable, mark_complete]"
            )
        valid_values = [e.value for e in ProjectActionEnum]
        if action not in valid_values:
            raise InvalidParameterError(
                f"action must be one of {valid_values}"
            )

    @staticmethod
    def _parse_uuid_csv(value: str | None) -> list[uuid.UUID] | None:
        """Parse comma-separated UUID values, skipping invalid ones."""
        if not value or not value.strip():
            return None

        valid_uuids: list[uuid.UUID] = []
        for item in value.split(","):
            item = item.strip()
            try:
                valid_uuids.append(uuid.UUID(item))
            except (ValueError, AttributeError):
                continue

        return valid_uuids if valid_uuids else None

    @staticmethod
    def _parse_csv(value: str | None) -> list[str] | None:
        """Parse comma-separated string values."""
        if not value or not value.strip():
            return None

        items = [item.strip() for item in value.split(",") if item.strip()]
        return items if items else None

    @staticmethod
    def _determine_repo_status(repo) -> str:
        """Determine repository status based on success rate.

        Args:
            repo: Repository ORM object.

        Returns:
            PASSED if success_rate > 0, FAILED otherwise.
        """
        if repo.pipeline_runs_count and repo.pipeline_runs_count > 0:
            if repo.success_rate and repo.success_rate > 0:
                return "PASSED"
            return "FAILED"
        return "PASSED"

    @staticmethod
    def _calculate_at_risk_overdue(project, repo_items: list) -> int:
        """Calculate the number of overdue days for an at-risk project.

        A project is considered at-risk overdue when it has been onboarded
        but has no repositories yet. The overdue count is the number of days
        since onboarding.

        Args:
            project: Project ORM object.
            repo_items: List of repository response items for the project.

        Returns:
            Number of overdue days, or 0 if not at risk.
        """
        if repo_items:
            return 0
        days_since_onboarding = (datetime.utcnow().date() - project.onboarded_date).days
        return max(days_since_onboarding, 0)
