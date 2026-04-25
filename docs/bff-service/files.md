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
| `app/api/analytics.py` | `/api/analytics/*`; в т.ч. `export/pdf`, `share-invites`, `chat-invites`, `clone-for-me`, `meta`. |
| `app/api/notification.py` | `/api/notification/*` |
| `app/api/report_tasks.py` | `/api/report-tasks` (прокси report-task-service; см. main). |
| `app/api/websocket.py` | `/api/websocket/*`; входящий `delete_chat_messages` (хвост от якоря или до 32 `message_ids`), `chat_messages_deleted` в `chat:{cid}`. См. [../frontend/nl-chat-and-reports.md](../frontend/nl-chat-and-reports.md). |
| `app/services/nl_chat_pdf.py` | Генерация PDF ответа assistant (шрифты, таблица/график из транскрипта). |
| `app/services/analytics_service.py` | `AnalyticsProxy`: прокси в analytics, включая `chat-suggestions` и операции с NL-чатом. |
| `app/services/chat_mq.py` | RabbitMQ для NL-чата. |
| `app/services/analytics_mq_consumer.py` | Очередь результатов SQL для UI. |
| `app/middleware/rate_limit.py` | Redis rate limit. |
| `app/middleware/request_audit.py` | Аудит. |
