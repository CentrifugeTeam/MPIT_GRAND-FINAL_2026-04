from fastapi import APIRouter, HTTPException, Depends, status
from app.api.auth import get_current_user
from app.schemas.notification import (
    NotificationCreate,
    NotificationResponse,
    NotificationListResponse,
    NotificationSettings,
    NotificationSettingsResponse
)
from app.services.notification_service import NotificationService

router = APIRouter()
notification_service = NotificationService()

@router.post("/{user_id}", response_model=NotificationResponse)
async def create_notification(
    user_id: str,
    notification_data: NotificationCreate,
    current_user: dict = Depends(get_current_user)
):
    """Создать уведомление для пользователя"""
    try:
        if current_user.get("uuid") != user_id and current_user.get("role") != "ADMIN":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )

        notification_data_with_email = notification_data.dict()
        notification_data_with_email["email"] = current_user.get("email")

        notification = await notification_service.create_notification(
            user_id,
            notification_data_with_email
        )
        return notification
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/{user_id}", response_model=NotificationListResponse)
async def get_user_notifications(
    user_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Получить все уведомления пользователя"""
    try:
        if current_user.get("uuid") != user_id and current_user.get("role") != "ADMIN":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )

        response = await notification_service.get_user_notifications(user_id)
        return NotificationListResponse(notifications=response.get("notifications", []))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get notifications"
        )

@router.post("/{user_id}/notify", response_model=dict)
async def send_notification(
    user_id: str,
    notification_data: NotificationCreate,
    current_user: dict = Depends(get_current_user)
):
    """Отправить уведомление в очередь RabbitMQ"""
    try:
        if current_user.get("uuid") != user_id and current_user.get("role") != "ADMIN":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )

        notification_data_with_email = notification_data.dict()
        notification_data_with_email["email"] = current_user.get("email")

        result = await notification_service.send_notification_to_queue(
            user_id,
            notification_data_with_email
        )
        return {"message": "Notification sent to queue", "notification_id": result}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/{user_id}/settings", response_model=NotificationSettingsResponse)
async def get_notification_settings(
    user_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Получить настройки уведомлений пользователя"""
    try:
        if current_user.get("uuid") != user_id and current_user.get("role") != "ADMIN":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )

        settings = await notification_service.get_notification_settings(user_id)
        return settings
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get notification settings: {str(e)}"
        )

@router.post("/{user_id}/settings", response_model=NotificationSettingsResponse)
async def update_notification_settings(
    user_id: str,
    settings_data: NotificationSettings,
    current_user: dict = Depends(get_current_user)
):
    """Обновить настройки уведомлений пользователя"""
    try:
        if current_user.get("uuid") != user_id and current_user.get("role") != "ADMIN":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )

        updated_settings = await notification_service.update_notification_settings(
            user_id,
            settings_data.dict()
        )
        return updated_settings
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
