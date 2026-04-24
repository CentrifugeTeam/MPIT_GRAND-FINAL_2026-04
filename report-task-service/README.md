# Report task service

Управление **расписаниями и прогонами отчётов**: хранение задач в platform PostgreSQL, диспетчер, постановка прогонов в очередь **`report_task_incoming_v1`** для **nl-orchestrator-worker**.

## Контракты

- **Порт (compose):** `8010`
- Внутренние вызовы: заголовок/токен `REPORT_TASK_INTERNAL_TOKEN` (BFF, оркестратор).

## Переменные окружения

См. `app/core/config.py`: `DATABASE_URL`, RabbitMQ, токены, upstream URL при необходимости.

## Документация

Архитектура, модули, API: [docs/report-task-service/README.md](../docs/report-task-service/README.md).
