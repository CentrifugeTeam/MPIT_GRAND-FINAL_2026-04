# report-task-service

## Зачем нужен

Управление **расписаниями и прогонами отчётов**: хранение задач в platform PostgreSQL, периодический диспетчер, постановка прогонов в очередь **`report_task_incoming_v1`** для обработки **nl-orchestrator-worker** (связка с NL/аналитикой по задумке кейса).

## Контракты

- **Порт:** `8010`
- **Префикс HTTP:** `/api/reports` (задачи, прогоны, шаблоны; см. роутеры `tasks`, `templates` в сервисе). Swagger: `/docs`.
- Внутренние вызовы защищаются токеном `REPORT_TASK_INTERNAL_TOKEN` (BFF и оркестратор передают его при необходимости). С фронта отчёты проксируются через BFF префикс **`/api/report-tasks`** (имя шлюза отличается от upstream-пути).

## Зависимости

- `postgres-db`, RabbitMQ.

## Исходники

Код: [`../../report-task-service/`](../../report-task-service/) · краткий [`README.md`](../../report-task-service/README.md) в каталоге сервиса.

Детали: [architecture.md](architecture.md), [modules.md](modules.md), [files.md](files.md).
