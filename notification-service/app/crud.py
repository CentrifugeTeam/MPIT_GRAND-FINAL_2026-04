from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from app.models import Notification, NotificationSettings, NotificationStatus
from app.schemas import NotificationCreate, NotificationSettings as NotificationSettingsSchema

class NotificationCRUD:
    def create_notification(self, db: Session, user_id: str, notification: NotificationCreate) -> Notification:
        """Создать уведомление"""
        db_notification = Notification(
            user_id=user_id,
            type=notification.type,
            title=notification.title,
            message=notification.message,
            email=notification.email
        )
        db.add(db_notification)
        db.commit()
        db.refresh(db_notification)
        return db_notification

    def get_user_notifications(self, db: Session, user_id: str, skip: int = 0, limit: int = 100) -> List[Notification]:
        """Получить уведомления пользователя"""
        return db.query(Notification).filter(
            Notification.user_id == user_id
        ).offset(skip).limit(limit).all()

    def get_notification_by_id(self, db: Session, notification_id: UUID) -> Optional[Notification]:
        """Получить уведомление по ID"""
        return db.query(Notification).filter(Notification.id == notification_id).first()

    def update_notification_status(self, db: Session, notification_id: UUID, status: NotificationStatus, error_message: Optional[str] = None) -> Optional[Notification]:
        """Обновить статус уведомления"""
        db_notification = self.get_notification_by_id(db, notification_id)
        if not db_notification:
            return None

        db_notification.status = status
        if error_message:
            db_notification.error_message = error_message

        db.commit()
        db.refresh(db_notification)
        return db_notification

    def get_pending_notifications(self, db: Session, limit: int = 100) -> List[Notification]:
        """Получить уведомления в статусе PENDING"""
        return db.query(Notification).filter(
            Notification.status == NotificationStatus.PENDING
        ).limit(limit).all()

class NotificationSettingsCRUD:
    def get_user_settings(self, db: Session, user_id: str) -> Optional[NotificationSettings]:
        """Получить настройки уведомлений пользователя"""
        return db.query(NotificationSettings).filter(NotificationSettings.user_id == user_id).first()

    def create_or_update_settings(self, db: Session, user_id: str, settings: NotificationSettingsSchema) -> NotificationSettings:
        """Создать или обновить настройки уведомлений"""
        existing_settings = self.get_user_settings(db, user_id)

        if existing_settings:
            existing_settings.email_notifications = settings.email_notifications
            existing_settings.system_notifications = settings.system_notifications
            existing_settings.registration_notifications = settings.registration_notifications
            db.commit()
            db.refresh(existing_settings)
            return existing_settings
        else:
            db_settings = NotificationSettings(
                user_id=user_id,
                email_notifications=settings.email_notifications,
                system_notifications=settings.system_notifications,
                registration_notifications=settings.registration_notifications
            )
            db.add(db_settings)
            db.commit()
            db.refresh(db_settings)
            return db_settings

notification_crud = NotificationCRUD()
notification_settings_crud = NotificationSettingsCRUD()
