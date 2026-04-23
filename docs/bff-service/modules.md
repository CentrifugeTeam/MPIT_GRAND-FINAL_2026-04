# bff-service — модули

| Путь | Назначение |
|------|------------|
| `app/main.py` | FastAPI, middleware, роутеры, lifespan (MQ + Redis). |
| `app/core/config.py` | Настройки URL сервисов, Redis, RabbitMQ, SMTP. |
| `app/core/queues.py` | Имена очередей RabbitMQ (общие с воркерами). |
| `app/core/connection_manager.py` | Управление WebSocket-подключениями. |
| `app/middleware/request_audit.py` | Структурированный аудит HTTP в stdout. |
| `app/middleware/rate_limit.py` | Лимит запросов на JWT user или IP. |
| `app/api/auth.py` | Прокси к auth-service. |
| `app/api/analytics.py` | Прокси к analytics-service + заголовки пользователя. |
| `app/api/notification.py` | Прокси к notification-service. |
| `app/api/report_tasks.py` | Прокси к report-task-service. |
| `app/api/websocket.py` | HTTP-вспомогательные эндпоинты для WS. |
| `app/services/auth_service.py` | HTTP-клиент к auth. |
| `app/services/analytics_service.py` | HTTP-клиент к analytics. |
| `app/services/analytics_schema_client.py` | Загрузка схемы для чата. |
| `app/services/notification_service.py` | HTTP к notifications. |
| `app/services/chat_mq.py` | Публикация/подписка чата в RabbitMQ. |
| `app/services/analytics_mq_consumer.py` | Consumer `nl_sql_generate_result`. |
| `app/services/websocket_service.py` | Связка WS с бизнес-событиями. |
| `app/schemas/*` | Pydantic-схемы, в т.ч. дублирование OpenAPI upstream. |
