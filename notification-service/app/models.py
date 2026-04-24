from sqlalchemy import Column, String, Boolean, DateTime, Text, Enum as SAEnum, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from app.database import Base
import enum

class NotificationType(str, enum.Enum):
    REGISTRATION = "registration"
    SYSTEM = "system"
    EMAIL = "email"
    REPORT = "report"
    CHAT_INVITE = "chat_invite"

class NotificationStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"

def _enum_values(enum_cls):
    return [e.value for e in enum_cls]


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    type = Column(
        SAEnum(
            NotificationType,
            name="notificationtype",
            values_callable=_enum_values,
        ),
        nullable=False,
    )
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    payload = Column(JSONB, nullable=True)
    status = Column(
        SAEnum(
            NotificationStatus,
            name="notificationstatus",
            values_callable=_enum_values,
        ),
        default=NotificationStatus.PENDING,
        nullable=False,
    )
    email = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    sent_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)

class NotificationSettings(Base):
    __tablename__ = "notification_settings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), unique=True, nullable=False, index=True)
    email_notifications = Column(Boolean, default=True, nullable=False)
    system_notifications = Column(Boolean, default=True, nullable=False)
    registration_notifications = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
