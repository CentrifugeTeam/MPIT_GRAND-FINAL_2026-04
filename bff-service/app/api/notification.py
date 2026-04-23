from fastapi import APIRouter, HTTPException, Depends, status
from app.api.auth import get_current_user
from app.schemas.notification import (
    NotificationCreate,
    NotificationResponse,
    NotificationListResponse,
    NotificationSettings,
    NotificationSettingsResponse,
    NotifyEnqueueResponse,
)
from app.services.notification_service import NotificationService

router = APIRouter()
notification_service = NotificationService()


@router.post(
    "/{user_id}",
    response_model=NotificationResponse,
    summary="Создать уведомление",
    description="Свой user_id или ADMIN. Email подмешивается из JWT.",
    responses={403: {"description": "Чужой user_id"}, 400: {"description": "Ошибка notification-service"}},
)
async def create_notification(
    user_id: str,
    notification_data: NotificationCreate,
    current_user: dict = Depends(get_current_user),
):
    try:
        if current_user.get("uuid") != user_id and current_user.get("role") != "ADMIN":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
            )

        notification_data_with_email = notification_data.model_dump()
        notification_data_with_email["email"] = current_user.get("email")

        notification = await notification_service.create_notification(
            user_id,
            notification_data_with_email,
        )
        return notification
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/{user_id}",
    response_model=NotificationListResponse,
    summary="Список уведомлений пользователя",
    description="Свой user_id или ADMIN.",
    responses={403: {"description": "Чужой user_id"}},
)
async def get_user_notifications(
    user_id: str,
    current_user: dict = Depends(get_current_user),
):
    try:
        if current_user.get("uuid") != user_id and current_user.get("role") != "ADMIN":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
            )

        response = await notification_service.get_user_notifications(user_id)
        return NotificationListResponse(notifications=response.get("notifications", []))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get notifications",
        )


@router.post(
    "/{user_id}/notify",
    response_model=NotifyEnqueueResponse,
    summary="Поставить уведомление в очередь RabbitMQ",
    description="Асинхронная доставка через notification-worker.",
    responses={403: {"description": "Чужой user_id"}},
)
async def send_notification(
    user_id: str,
    notification_data: NotificationCreate,
    current_user: dict = Depends(get_current_user),
):
    try:
        if current_user.get("uuid") != user_id and current_user.get("role") != "ADMIN":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
            )

        notification_data_with_email = notification_data.model_dump()
        notification_data_with_email["email"] = current_user.get("email")

        result = await notification_service.send_notification_to_queue(
            user_id,
            notification_data_with_email,
        )
        nid = str(result) if result is not None else ""
        return NotifyEnqueueResponse(
            message="Notification sent to queue",
            notification_id=nid,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/{user_id}/settings",
    response_model=NotificationSettingsResponse,
    summary="Настройки уведомлений",
    description="Свой user_id или ADMIN.",
    responses={403: {"description": "Чужой user_id"}},
)
async def get_notification_settings(
    user_id: str,
    current_user: dict = Depends(get_current_user),
):
    try:
        if current_user.get("uuid") != user_id and current_user.get("role") != "ADMIN":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
            )

        settings_out = await notification_service.get_notification_settings(user_id)
        return settings_out
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get notification settings: {str(e)}",
        )


@router.post(
    "/{user_id}/settings",
    response_model=NotificationSettingsResponse,
    summary="Обновить настройки уведомлений",
    description="Свой user_id или ADMIN.",
    responses={403: {"description": "Чужой user_id"}},
)
async def update_notification_settings(
    user_id: str,
    settings_data: NotificationSettings,
    current_user: dict = Depends(get_current_user),
):
    try:
        if current_user.get("uuid") != user_id and current_user.get("role") != "ADMIN":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
            )

        updated_settings = await notification_service.update_notification_settings(
            user_id,
            settings_data.model_dump(),
        )
        return updated_settings
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
