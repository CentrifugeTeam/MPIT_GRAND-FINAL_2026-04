import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (
    NotificationCreate,
    NotificationResponse,
    NotificationListResponse,
    NotificationSettings,
    NotificationSettingsResponse,
    NotifyEnqueueResponse,
)
from app.crud import notification_crud, notification_settings_crud
from app.services.rabbitmq_service import RabbitMQService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/{user_id}",
    response_model=NotificationResponse,
    summary="Создать уведомление в БД",
    description="Сохраняет запись без отправки в очередь.",
)
async def create_notification(
    user_id: str,
    notification: NotificationCreate,
    db: Session = Depends(get_db),
):
    try:
        db_notification = notification_crud.create_notification(db, user_id, notification)
        return NotificationResponse.model_validate(db_notification)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/{user_id}",
    response_model=NotificationListResponse,
    summary="Список уведомлений пользователя",
    description="Пагинация skip/limit.",
)
async def get_user_notifications(
    user_id: str,
    skip: int = Query(0, ge=0, description="Пропустить записей"),
    limit: int = Query(100, ge=1, le=500, description="Максимум записей"),
    db: Session = Depends(get_db),
):
    try:
        notifications = notification_crud.get_user_notifications(db, user_id, skip, limit)
        return NotificationListResponse(
            notifications=[NotificationResponse.model_validate(n) for n in notifications],
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get notifications",
        )


@router.get(
    "/{user_id}/settings",
    response_model=NotificationSettingsResponse,
    summary="Настройки уведомлений",
    description="При отсутствии записи создаются значения по умолчанию.",
)
async def get_notification_settings(
    user_id: str,
    db: Session = Depends(get_db),
):
    try:
        settings = notification_settings_crud.get_user_settings(db, user_id)
        if not settings:
            default_settings = NotificationSettings()
            settings = notification_settings_crud.create_or_update_settings(
                db, user_id, default_settings
            )

        return NotificationSettingsResponse.model_validate(settings)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get notification settings",
        )


@router.post(
    "/{user_id}/settings",
    response_model=NotificationSettingsResponse,
    summary="Обновить настройки уведомлений",
)
async def update_notification_settings(
    user_id: str,
    settings: NotificationSettings,
    db: Session = Depends(get_db),
):
    try:
        updated_settings = notification_settings_crud.create_or_update_settings(
            db, user_id, settings
        )
        return NotificationSettingsResponse.model_validate(updated_settings)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/{user_id}/notify",
    response_model=NotifyEnqueueResponse,
    summary="Поставить уведомление в очередь RabbitMQ",
    description="Создаёт запись в БД и публикует сообщение в email_queue.",
)
async def send_notification_to_queue(
    user_id: str,
    notification: NotificationCreate,
    db: Session = Depends(get_db),
):
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
                "email": notification.email,
            }

            rabbitmq_service.publish_message("email_queue", message)
        except Exception as rabbitmq_error:
            logger.exception("Failed to publish notification to RabbitMQ")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Failed to enqueue notification: {rabbitmq_error}",
            )

        return NotifyEnqueueResponse(
            message="Notification sent to queue",
            notification_id=str(db_notification.id),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send notification: {str(e)}",
        )
