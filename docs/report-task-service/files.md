# report-task-service — ключевые файлы

Относительно [`report-task-service/`](../../report-task-service/).

| Путь | Роль |
|------|------|
| `Dockerfile` | Образ. |
| `app/main.py` | Точка входа. |
| `app/core/config.py` | Env. |
| `app/core/queues.py` | `report_task_incoming_v1`. |
| `app/api/tasks.py` | HTTP API отчётов. |
| `app/services/scheduler.py` | Фоновый dispatch. |
| `app/services/rabbitmq_publish.py` | Отправка в очередь. |
| `app/db/models.py` | Таблицы. |
| `app/db/session.py` | Подключение к БД. |
