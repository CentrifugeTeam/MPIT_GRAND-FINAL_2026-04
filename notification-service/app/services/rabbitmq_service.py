import pika
import json
import asyncio
from typing import Dict, Any
from app.core.config import get_settings
from app.database import SessionLocal
from app.crud import notification_crud, notification_settings_crud
from app.services.email_service import email_service
from app.models import NotificationStatus

settings = get_settings()

class RabbitMQService:
    def __init__(self):
        self.connection = None
        self.channel = None
        self.queue_name = "email_queue"

    def connect(self):
        """Подключиться к RabbitMQ"""
        try:
            credentials = pika.PlainCredentials(settings.RABBITMQ_USER, settings.RABBITMQ_PASSWORD)
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=settings.RABBITMQ_HOST,
                    credentials=credentials
                )
            )
            self.channel = self.connection.channel()

            # Объявляем очередь
            self.channel.queue_declare(queue=self.queue_name, durable=True)
        except Exception as e:
            pass

    def disconnect(self):
        """Отключиться от RabbitMQ"""
        if self.connection and not self.connection.is_closed:
            self.connection.close()

    def publish_message(self, queue_name: str, message: Dict[str, Any]):
        """Опубликовать сообщение в очередь"""
        try:
            # Подключаемся если не подключены
            if not self.connection or self.connection.is_closed:
                self.connect()

            self.channel.basic_publish(
                exchange="",
                routing_key=queue_name,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Сделать сообщение постоянным
                )
            )

        except Exception as e:
            raise e

    def consume_messages(self, callback_func=None):
        """Потреблять сообщения из очереди"""
        def callback(ch, method, properties, body):
            try:
                message = json.loads(body)
                # Обрабатываем сообщение
                if callback_func:
                    asyncio.run(callback_func(message))
                else:
                    self.process_notification(message)

                ch.basic_ack(delivery_tag=method.delivery_tag)
            except Exception as e:
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

        try:
            self.channel.basic_qos(prefetch_count=1)
            self.channel.basic_consume(
                queue=self.queue_name,
                on_message_callback=callback
            )
            self.channel.start_consuming()
        except Exception as e:
            pass

    def process_notification(self, message: Dict[str, Any]):
        """Обработать уведомление"""
        db = SessionLocal()
        try:
            user_id = message.get("user_id")
            notification_type = message.get("type")
            title = message.get("title")
            message_text = message.get("message")
            email = message.get("email")

            # Получаем настройки пользователя
            settings = notification_settings_crud.get_user_settings(db, user_id)

            # Проверяем, разрешены ли уведомления данного типа
            if settings:
                if notification_type == "registration" and not settings.registration_notifications:
                    return
                elif notification_type == "system" and not settings.system_notifications:
                    return
                elif notification_type == "email" and not settings.email_notifications:
                    return

            # Отправляем email
            if email:
                success = False
                if notification_type == "registration":
                    success = email_service.send_registration_email(email)
                else:
                    success = email_service.send_system_notification(email, title, message_text)

                # Обновляем статус уведомления
                if success:
                    # Находим уведомление по user_id и типу
                    notifications = notification_crud.get_user_notifications(db, user_id)
                    for notification in notifications:
                        if (notification.type == notification_type and
                            notification.status == NotificationStatus.PENDING):
                            notification_crud.update_notification_status(
                                db, notification.id, NotificationStatus.SENT
                            )
                            break
                else:
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
            pass
        finally:
            db.close()

# Создаем экземпляр сервиса
rabbitmq_service = RabbitMQService()
