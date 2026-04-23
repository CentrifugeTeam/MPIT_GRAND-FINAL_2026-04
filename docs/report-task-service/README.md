# report-task-service

## Зачем нужен

Управление **расписаниями и прогонами отчётов**: хранение задач в platform PostgreSQL, периодический диспетчер, постановка прогонов в очередь **`report_task_incoming_v1`** для обработки **nl-orchestrator-worker** (связка с NL/аналитикой по задумке кейса).

## Контракты

- **Порт:** `8010`
- Внутренние вызовы защищаются токеном `REPORT_TASK_INTERNAL_TOKEN` (BFF и оркестратор передают его при необходимости).

## Зависимости

- `postgres-db`, RabbitMQ.

## Исходники

[`../../report-task-service/`](../../report-task-service/).

Детали: [architecture.md](architecture.md), [modules.md](modules.md), [files.md](files.md).
