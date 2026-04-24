# sql-generator-worker

## Зачем нужен

**Фоновый исполнитель генерации и выполнения SQL:** читает задания из **`nl_sql_generate_request`**, вызывает LLM при необходимости, валидирует и выполняет запросы к warehouse, публикует результат в **`nl_sql_generate_result`** (для BFF/UI) и **`nl_sql_generate_result_chat`** (для nl-orchestrator-worker в сценарии чата).

## Границы

- Не открывает публичный HTTP API в compose — только RabbitMQ + БД.
- Использует те же лимиты безопасности SQL, что и analytics (guardrails, timeouts).

## Зависимости

- `main-db`, `postgres-db` (платформа для job-статусов через `job_db`), RabbitMQ, LLM API.

## Исходники

Код: [`../../sql-generator-worker/`](../../sql-generator-worker/) · краткий [`README.md`](../../sql-generator-worker/README.md) в каталоге воркера.

Детали: [architecture.md](architecture.md), [modules.md](modules.md), [files.md](files.md).
