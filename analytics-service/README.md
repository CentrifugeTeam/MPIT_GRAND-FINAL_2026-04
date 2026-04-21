# Analytics service (NL → SQL)

## HTTP API (актуально)

- `GET /api/analytics/schema` — схема `public` для BFF (подстановка в `chat_message`) и кэш; cron `SCHEMA_CRON_HOUR` UTC.
- `POST /api/analytics/interpret-question` — эвристика вопроса + глоссарий для NL-чата (без задачи в очереди).
- История и чаты: `GET/DELETE /api/analytics/history`, `POST /api/analytics/chats`, `GET/PATCH/DELETE /api/analytics/chats/{id}[/messages]`.
- `DELETE /api/analytics/jobs/{job_id}` — удалить старую запись `sql_job` из истории.
- `POST /api/analytics/internal/nl-chat-sync` — только для **nl-orchestrator-worker** (токен `X-Chat-Sync-Token`).

Постановка SQL в очередь **не** через этот сервис: сообщение в **`nl_sql_generate_request`** публикует **nl-orchestrator-worker** после `chat_message`.

## Переменные окружения

См. `app/core/config.py`: `ANALYTICS_DATABASE_URL` / платформа, RabbitMQ (опционально для будущих сценариев), лимиты запросов, `INTERNAL_NL_CHAT_SYNC_TOKEN`.
