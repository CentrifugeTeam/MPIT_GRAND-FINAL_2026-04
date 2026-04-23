# notification-service — модули

| Путь | Назначение |
|------|------------|
| `app/main.py` | FastAPI приложение. |
| `app/core/config.py` | Настройки БД и RabbitMQ. |
| `app/api/notifications.py` | Эндпоинты уведомлений и постановки в очередь. |
| `app/schemas.py` | Pydantic-схемы. |
| `app/models.py` | ORM уведомлений. |
| `app/database.py` | Подключение к PostgreSQL. |
| `app/crud.py` | Запись/чтение уведомлений. |
| `app/services/rabbitmq_service.py` | Синхронный pika: declare `email_queue`, publish, consume в воркере. |
| `app/services/email_service.py` | Отправка через SMTP. |
| `email_worker.py` | Entrypoint второго контейнера: цикл consumer. |
| `worker.py` | Дополнительный/legacy воркер (сверить с командой в compose). |
