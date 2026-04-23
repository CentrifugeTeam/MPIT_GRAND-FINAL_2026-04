from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, EmailStr

from app.models import NotificationType, NotificationStatus


class NotificationCreate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "type": "report",
                "title": "Отчёт",
                "message": "Сводка готова",
                "email": "user@example.com",
            },
        },
    )
    type: NotificationType = Field(..., description="Тип уведомления")
    title: str = Field(..., min_length=1, description="Заголовок")
    message: str = Field(..., min_length=1, description="Текст")
    email: Optional[EmailStr] = Field(default=None, description="Почта получателя (опционально)")


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: str
    type: NotificationType
    title: str
    message: str
    status: NotificationStatus
    email: Optional[str]
    created_at: datetime
    sent_at: Optional[datetime] = None
    error_message: Optional[str] = None


class NotificationListResponse(BaseModel):
    notifications: List[NotificationResponse] = Field(
        default_factory=list,
        description="Список уведомлений",
    )


class NotificationSettings(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email_notifications": True,
                "system_notifications": True,
                "registration_notifications": True,
            },
        },
    )
    email_notifications: bool = Field(default=True, description="Email-уведомления")
    system_notifications: bool = Field(default=True, description="Системные")
    registration_notifications: bool = Field(default=True, description="О регистрации")


class NotificationSettingsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    email_notifications: bool
    system_notifications: bool
    registration_notifications: bool
    created_at: datetime
    updated_at: Optional[datetime] = None


class NotifyEnqueueResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {"message": "Notification sent to queue", "notification_id": "..."},
        },
    )
    message: str = Field(..., description="Статус постановки в очередь")
    notification_id: str = Field(..., description="ID записи уведомления")
