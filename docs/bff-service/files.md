# bff-service — ключевые файлы

Относительно [`bff-service/`](../../bff-service/).

| Путь | Роль |
|------|------|
| `Dockerfile` | Образ приложения. |
| `app/main.py` | Точка входа, подключение роутеров и middleware. |
| `app/core/config.py` | Все URL и секреты окружения. |
| `app/core/queues.py` | Константы имён очередей. |
| `app/core/connection_manager.py` | Реестр активных WebSocket. |
| `app/api/auth.py` | `/api/auth/*` |
| `app/api/analytics.py` | `/api/analytics/*` |
| `app/api/notification.py` | `/api/notification/*` |
| `app/api/report_tasks.py` | `/api/report-tasks` (прокси report-task-service; см. main). |
| `app/api/websocket.py` | `/api/websocket/*` |
| `app/services/chat_mq.py` | RabbitMQ для NL-чата. |
| `app/services/analytics_mq_consumer.py` | Очередь результатов SQL для UI. |
| `app/middleware/rate_limit.py` | Redis rate limit. |
| `app/middleware/request_audit.py` | Аудит. |
