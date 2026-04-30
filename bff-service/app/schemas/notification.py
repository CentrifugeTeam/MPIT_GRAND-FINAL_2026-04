from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from pydantic import EmailStr
from datetime import datetime
from enum import Enum

class NotificationType(str, Enum):
    REGISTRATION = "registration"
    SYSTEM = "system"
    EMAIL = "email"
    REPORT = "report"
    CHAT_INVITE = "chat_invite"

class NotificationStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"

class NotifyEnqueueResponse(BaseModel):
    """Ответ после постановки уведомления в очередь RabbitMQ."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"message": "Notification sent to queue", "notification_id": "uuid-or-id"},
        },
    )
    message: str = Field(..., description="Статус операции")
    notification_id: str = Field(..., description="Идентификатор, возвращённый notification-service")


class NotificationCreate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "type": "report",
                "title": "Отчет по заказам",
                "message": "Краткая сводка за неделю готова.",
            }
        }
    )
    type: NotificationType = Field(..., description="Тип уведомления")
    title: str = Field(..., min_length=1, description="Заголовок")
    message: str = Field(..., min_length=1, description="Текст уведомления")
    email: Optional[EmailStr] = Field(default=None, description="Email получателя (опционально)")
    payload: Optional[dict] = Field(default=None, description="Дополнительные данные уведомления")

class NotificationResponse(BaseModel):
    id: str
    user_id: str
    type: NotificationType
    title: str
    message: str
    payload: Optional[dict] = None
    status: NotificationStatus
    created_at: datetime
    sent_at: Optional[datetime] = None

class NotificationListResponse(BaseModel):
    notifications: List[NotificationResponse]

class NotificationSettings(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email_notifications": True,
                "system_notifications": True,
                "registration_notifications": True,
            }
        }
    )
    email_notifications: bool = True
    system_notifications: bool = True
    registration_notifications: bool = True

class NotificationSettingsResponse(BaseModel):
    user_id: str
    email_notifications: bool
    system_notifications: bool
    registration_notifications: bool
    updated_at: datetime
