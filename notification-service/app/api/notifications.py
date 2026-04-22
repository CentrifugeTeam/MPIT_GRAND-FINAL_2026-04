from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas import (
    NotificationCreate,
    NotificationResponse,
    NotificationListResponse,
    NotificationSettings,
    NotificationSettingsResponse
)
from app.crud import notification_crud, notification_settings_crud
from app.services.rabbitmq_service import RabbitMQService
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/{user_id}", response_model=NotificationResponse)
async def create_notification(
    user_id: str,
    notification: NotificationCreate,
    db: Session = Depends(get_db)
):
    """Создать уведомление для пользователя"""
    try:
        db_notification = notification_crud.create_notification(db, user_id, notification)
        return NotificationResponse.from_orm(db_notification)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/{user_id}", response_model=NotificationListResponse)
async def get_user_notifications(
    user_id: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Получить все уведомления пользователя"""
    try:
        notifications = notification_crud.get_user_notifications(db, user_id, skip, limit)
        return NotificationListResponse(
            notifications=[NotificationResponse.from_orm(notification) for notification in notifications]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get notifications"
        )

@router.get("/{user_id}/settings", response_model=NotificationSettingsResponse)
async def get_notification_settings(
    user_id: str,
    db: Session = Depends(get_db)
):
    """Получить настройки уведомлений пользователя"""
    try:
        settings = notification_settings_crud.get_user_settings(db, user_id)
        if not settings:
            default_settings = NotificationSettings()
            settings = notification_settings_crud.create_or_update_settings(
                db, user_id, default_settings
            )

        return NotificationSettingsResponse.from_orm(settings)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get notification settings"
        )

@router.post("/{user_id}/settings", response_model=NotificationSettingsResponse)
async def update_notification_settings(
    user_id: str,
    settings: NotificationSettings,
    db: Session = Depends(get_db)
):
    """Обновить настройки уведомлений пользователя"""
    try:
        updated_settings = notification_settings_crud.create_or_update_settings(
            db, user_id, settings
        )
        return NotificationSettingsResponse.from_orm(updated_settings)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/{user_id}/notify")
async def send_notification_to_queue(
    user_id: str,
    notification: NotificationCreate,
    db: Session = Depends(get_db)
):
    """Отправить уведомление в очередь RabbitMQ"""
    try:
        db_notification = notification_crud.create_notification(db, user_id, notification)

        try:
            rabbitmq_service = RabbitMQService()
            message = {
                "notification_id": str(db_notification.id),
                "user_id": user_id,
                "type": notification.type,
                "title": notification.title,
                "message": notification.message,
                "email": notification.email
            }

            rabbitmq_service.publish_message("email_queue", message)
        except Exception as rabbitmq_error:
            logger.exception("Failed to publish notification to RabbitMQ")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Failed to enqueue notification: {rabbitmq_error}",
            )

        return {"message": "Notification sent to queue", "notification_id": str(db_notification.id)}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send notification: {str(e)}"
        )
