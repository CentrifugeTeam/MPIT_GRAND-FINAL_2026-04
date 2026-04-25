# bff-service

## Зачем нужен

**Единая точка входа** для фронтенда: один origin для HTTP (REST и **SSE** уведомлений), WebSocket (NL-чат), прокси к auth, analytics, report-task, notification; оркестрация заголовков `X-User-Id` / `X-User-Role`; интеграция с **RabbitMQ** для NL-чата и потребления результатов SQL-генерации.

## Границы ответственности

- Проксирование и агрегация REST API.
- WebSocket для NL-чата: публикация в `nl_chat_incoming`, чтение `nl_chat_out`.
- **SSE:** `GET /api/notification/stream` (токен в query) — поток in-app уведомлений; при Redis — pub/sub на обновления списка.
- Фоновый consumer очереди `nl_sql_generate_result` для доставки результатов в сессии WebSocket.
- **Экспорт ответа NL-чата в PDF:** не проксируется в analytics как готовый файл; BFF запрашивает транскрипт и собирает PDF локально (`app/services/nl_chat_pdf.py`, эндпоинт `GET /api/analytics/chats/{id}/export/pdf`).
- **Совместные чаты:** прокси к analytics для инвайтов и клона; при `POST .../share-invites` — дополнительно вызов notification-service (тип `CHAT_INVITE`) и Redis touch для обновления UI у приглашённых.
- Rate limit (Redis) и JSON-аудит запросов — см. middleware.

## Контракты

- **Порт:** `8000`
- **Префиксы:** `/api/auth`, `/api/notification`, `/api/analytics`, `/api/report-tasks`, `/api/websocket`
- Swagger: `/docs`

## Зависимости

- **HTTP upstream:** auth-service, analytics-service, report-task-service, notification-service; косвенно nl-orchestrator-worker через очереди (не HTTP из BFF).
- **RabbitMQ:** см. [../infrastructure/messaging.md](../infrastructure/messaging.md).
- **Redis (опционально):** rate limiting, публикация «touch» для in-app уведомлений при инвайтах в чат, канал для ветки SSE уведомлений.

## Конфигурация

Переменные с префиксами `AUTH_SERVICE_URL`, `ANALYTICS_SERVICE_URL`, `REPORT_TASK_SERVICE_URL`, `NOTIFICATION_SERVICE_URL`, `REDIS_URL`, `RABBITMQ_*`, `DEFAULT_ANALYTICS_SOURCE_KEY`, `NL_CHAT_BLOCKED_SOURCE_KEYS` — в [`.example.env`](../../.example.env).

## Исходники

[`../../bff-service/`](../../bff-service/) · локальный [README](../../bff-service/README.md).

Детали: [architecture.md](architecture.md), [modules.md](modules.md), [files.md](files.md).
