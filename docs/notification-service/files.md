# notification-service — ключевые файлы

Относительно [`notification-service/`](../../notification-service/).

| Путь | Роль |
|------|------|
| `Dockerfile` | Два stage/target; worker override в compose. |
| `app/main.py` | HTTP API. |
| `app/api/notifications.py` | Маршруты. |
| `app/services/rabbitmq_service.py` | Очередь email. |
| `app/services/email_service.py` | SMTP. |
| `email_worker.py` | Процесс воркера в Docker. |
| `worker.py` | См. использование в проекте. |
