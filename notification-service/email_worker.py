#!/usr/bin/env python3
"""
Email Worker для обработки уведомлений из RabbitMQ
"""
import asyncio
import json
import logging
from app.services.rabbitmq_service import rabbitmq_service
from app.services.email_service import email_service
from app.database import SessionLocal
from app.crud import notification_crud, notification_settings_crud
from app.models import NotificationStatus

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def process_notification(notification_data: dict):
    """Обработать уведомление"""
    db = SessionLocal()
    try:
        user_id = notification_data.get("user_id")
        notification_type = notification_data.get("type")
        title = notification_data.get("title")
        message = notification_data.get("message")
        email = notification_data.get("email")

        logger.info(f"Processing notification for user {user_id}: {title}")

        # Получаем настройки пользователя
        settings = notification_settings_crud.get_user_settings(db, user_id)

        # Проверяем, разрешены ли уведомления данного типа
        if settings:
            if notification_type == "registration" and not settings.registration_notifications:
                logger.info(f"Registration notifications disabled for user {user_id}")
                return
            elif notification_type == "system" and not settings.system_notifications:
                logger.info(f"System notifications disabled for user {user_id}")
                return
            elif notification_type == "email" and not settings.email_notifications:
                logger.info(f"Email notifications disabled for user {user_id}")
                return

        # Отправляем email
        if email:
            success = False
            try:
                if notification_type == "registration":
                    success = email_service.send_registration_email(email)
                else:
                    success = email_service.send_system_notification(email, title, message)

                if success:
                    logger.info(f"Email sent successfully to {email}")
                    # Обновляем статус уведомления на SENT
                    notifications = notification_crud.get_user_notifications(db, user_id)
                    for notification in notifications:
                        if (notification.type == notification_type and
                            notification.status == NotificationStatus.PENDING):
                            notification_crud.update_notification_status(
                                db, notification.id, NotificationStatus.SENT
                            )
                            break
                else:
                    logger.error(f"Failed to send email to {email}")
                    # Обновляем статус на FAILED
                    notifications = notification_crud.get_user_notifications(db, user_id)
                    for notification in notifications:
                        if (notification.type == notification_type and
                            notification.status == NotificationStatus.PENDING):
                            notification_crud.update_notification_status(
                                db, notification.id, NotificationStatus.FAILED,
                                "Failed to send email"
                            )
                            break
            except Exception as e:
                logger.error(f"Error sending email: {str(e)}")
                # Обновляем статус на FAILED
                notifications = notification_crud.get_user_notifications(db, user_id)
                for notification in notifications:
                    if (notification.type == notification_type and
                        notification.status == NotificationStatus.PENDING):
                        notification_crud.update_notification_status(
                            db, notification.id, NotificationStatus.FAILED,
                            f"Error: {str(e)}"
                        )
                        break
        else:
            logger.warning(f"No email provided for user {user_id}")

    except Exception as e:
        logger.error(f"Error processing notification: {str(e)}")
    finally:
        db.close()

def main():
    """Запуск email worker"""
    logger.info("Starting email worker...")

    try:
        # Подключаемся к RabbitMQ
        rabbitmq_service.connect()

        # Начинаем потреблять сообщения
        rabbitmq_service.consume_messages(process_notification)

    except KeyboardInterrupt:
        logger.info("Stopping email worker...")
    except Exception as e:
        logger.error(f"Email worker error: {str(e)}")
    finally:
        rabbitmq_service.disconnect()

if __name__ == "__main__":
    main()
