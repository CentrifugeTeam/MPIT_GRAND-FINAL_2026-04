from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from app.models import NotificationType, NotificationStatus

class NotificationCreate(BaseModel):
    type: NotificationType
    title: str
    message: str
    email: Optional[str] = None

class NotificationResponse(BaseModel):
    id: UUID
    user_id: str
    type: NotificationType
    title: str
    message: str
    status: NotificationStatus
    email: Optional[str]
    created_at: datetime
    sent_at: Optional[datetime]
    error_message: Optional[str]

    class Config:
        from_attributes = True

class NotificationListResponse(BaseModel):
    notifications: List[NotificationResponse]

class NotificationSettings(BaseModel):
    email_notifications: bool = True
    system_notifications: bool = True
    registration_notifications: bool = True

class NotificationSettingsResponse(BaseModel):
    user_id: str
    email_notifications: bool
    system_notifications: bool
    registration_notifications: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
