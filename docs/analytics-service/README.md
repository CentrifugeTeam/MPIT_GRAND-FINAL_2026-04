# analytics-service

## Зачем нужен

**Ядро аналитики и NL→SQL на уровне API и данных:** схемы БД по именованным источникам, интерпретация вопросов, история чатов, политики доступа, внутренний sync для оркестратора, **инвайты на совместный чат и клонирование** (данные в platform DB). Сообщение в очередь **`nl_sql_generate_request`** публикует **nl-orchestrator-worker**; выполнение SQL — в **sql-generator-worker** (см. upstream [README](../../analytics-service/README.md)).

## Границы ответственности

- Два подключения к БД: **warehouse** (`ANALYTICS_DATABASE_URL` / выбранный source) и **platform** (`PLATFORM_DATABASE_URL`).
- Модуль `rabbitmq_publish` зарезервирован под сценарии с MQ; постановка **`nl_sql_generate_request`** в текущей схеме — у оркестратора.
- Не является consumerом `nl_sql_generate_result` для BFF — это делает BFF; результаты для чата забирает nl-orchestrator из `nl_sql_generate_result_chat`.
- Генерация **PDF** по ответу чата на стороне analytics **не** реализована: транскрипт отдаётся REST, PDF строит BFF.

## Контракты

- **Порт:** `8009`
- **Префикс:** `/api/analytics` (основной роутер, источники данных, политики доступа для ADMIN), `/health`
- Swagger: `/docs`

## Зависимости

- `main-db`, `postgres-db`, RabbitMQ.
- LLM для interpret / quality (переменные `LLM_*`).

## Исходники

[`../../analytics-service/`](../../analytics-service/) · [README](../../analytics-service/README.md).

Детали: [architecture.md](architecture.md), [modules.md](modules.md), [files.md](files.md).
