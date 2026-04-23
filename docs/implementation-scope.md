# Реализованные возможности

Ниже — что есть в коде и compose сегодня (куда смотреть в репозитории и в доке по сервисам).

| Возможность | Где в проекте |
|-------------|----------------|
| Микросервисная архитектура, BFF для фронта | [bff-service](../bff-service/), [docs/bff-service/](bff-service/README.md) |
| Аутентификация и роли | [auth-service](../auth-service/), JWT, прокси через BFF |
| Две БД: платформа и витрина аналитики | [infrastructure/databases.md](infrastructure/databases.md), `docker-compose.yml` |
| Загрузка / сид витрины из CSV | `main-db-bootstrap`, [scripts/seed_main_db.py](../scripts/seed_main_db.py) |
| NL→SQL: схема БД, interpret, история чатов | [analytics-service](../analytics-service/), [docs/analytics-service/](analytics-service/README.md) |
| Асинхронная генерация SQL воркером | [sql-generator-worker](../sql-generator-worker/) — очередь `nl_sql_generate_request` (публикует nl-orchestrator-worker) |
| NL-чат с оркестрацией и LLM | [nl-orchestrator-worker](../nl-orchestrator-worker/), очереди `nl_chat_*` |
| WebSocket от UI через BFF | [bff-service/app/api/websocket.py](../bff-service/app/api/websocket.py), [frontend](frontend/modules.md) |
| Источники данных и политики доступа | [analytics-service/app/api/data_sources.py](../analytics-service/app/api/data_sources.py), `access_policies` |
| Отчётные задачи и расписание | [report-task-service](../report-task-service/), очередь `report_task_incoming_v1` |
| Уведомления по email через очередь | [notification-service](../notification-service/), `email_queue` и worker |
| Rate limit и аудит на шлюзе | [bff-service/app/middleware/](../bff-service/app/middleware/) |
| Nginx и опциональный CloudPub | [infrastructure/edge.md](infrastructure/edge.md) |
