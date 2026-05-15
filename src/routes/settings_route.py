"""Settings route for retrieving and updating specialization configuration."""

from fastapi import APIRouter, Depends

from src.models.base_response import BaseResponse
from src.models.settings_models import SettingsUpdateRequest
from src.services.dependencies import get_settings_service
from src.services.settings_service import SettingsService

router = APIRouter(prefix="")


@router.get("/settings/{specialization_id}")
async def get_settings(
    specialization_id: str,
    settings_service: SettingsService = Depends(get_settings_service),
) -> BaseResponse:
    """Retrieve settings for a specialization.

    Args:
        specialization_id: UUID of the specialization (path parameter).
        settings_service: Injected SettingsService instance.

    Returns:
        BaseResponse with settings data and email recipients.
    """
    settings_data = await settings_service.get_settings(specialization_id)

    return BaseResponse(
        status_code=200,
        status="success",
        message="Settings retrieved successfully",
        data=settings_data.model_dump(),
    )


@router.put("/settings/manage")
async def update_settings(
    request: SettingsUpdateRequest,
    settings_service: SettingsService = Depends(get_settings_service),
) -> BaseResponse:
    """Update settings for a specialization (partial update).

    Args:
        request: Settings update request body.
        settings_service: Injected SettingsService instance.

    Returns:
        BaseResponse with the updated settings data.
    """
    updated_data = await settings_service.update_settings(request)

    return BaseResponse(
        status_code=200,
        status="success",
        message="Settings updated successfully",
        data=updated_data.model_dump(),
    )
