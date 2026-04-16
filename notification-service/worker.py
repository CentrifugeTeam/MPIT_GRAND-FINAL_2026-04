#!/usr/bin/env python3
"""
Worker для обработки уведомлений из RabbitMQ
"""
import asyncio
from app.services.rabbitmq_service import rabbitmq_service

def main():
    """Запуск worker"""
    try:
        # Подключаемся к RabbitMQ
        rabbitmq_service.connect()

        # Начинаем потреблять сообщения
        rabbitmq_service.consume_messages()

    finally:
        rabbitmq_service.disconnect()

if __name__ == "__main__":
    main()
