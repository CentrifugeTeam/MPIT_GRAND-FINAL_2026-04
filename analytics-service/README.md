# Analytics service (NL → SQL)

## Синхронные ручки (как раньше)

- `GET /api/analytics/schema` — контекст БД (кэш 24 ч + ежедневный cron `SCHEMA_CRON_HOUR` UTC).
- `POST /api/analytics/generate-sql`, `/execute`, `/ask` — LLM/выполнение inline.

## Асинхронный пайплайн (как на схеме)

1. `POST /api/analytics/ask-async` — заголовок **`X-User-Id`** (ставит BFF из JWT): создаётся задача в `nl_sql_jobs`, шаблон из `template_parser`, сообщение в **`nl_sql_generate_request`**.
2. **sql-generator-worker** забирает задачу, вызывает LLM, guardrails, выполняет SQL, пишет результат в `nl_sql_jobs`, публикует в **`nl_sql_generate_result`**.
3. **BFF** слушает `nl_sql_generate_result` и шлёт клиенту WebSocket-сообщение `type: nl_sql_result` (комната `job:<job_id>` и дубль по `user_id`).

Опрос статуса: `GET /api/analytics/jobs/{job_id}` + заголовок `X-User-Id`.

## Переменные окружения

См. `app/core/config.py`: `PLATFORM_DATABASE_URL`, RabbitMQ, `LLM_*`, лимиты запросов.
