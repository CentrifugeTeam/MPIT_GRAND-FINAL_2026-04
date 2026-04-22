from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime
from enum import Enum

class NotificationType(str, Enum):
    REGISTRATION = "registration"
    SYSTEM = "system"
    EMAIL = "email"
    REPORT = "report"

class NotificationStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"

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
    type: NotificationType
    title: str
    message: str

class NotificationResponse(BaseModel):
    id: str
    user_id: str
    type: NotificationType
    title: str
    message: str
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
