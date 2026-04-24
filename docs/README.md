# Документация проекта

Корень репозитория с приложением: каталог с `docker-compose.yml`. Здесь — **вся** подробная документация (архитектура, контракты, сценарии). В каталогах **сервисов и приложения** в дереве кода — только **краткий `README.md`**: роль сервиса, порт, отсылка сюда. Длинные `*.md` в `bff-service/`, `frontend/` и т.п. не ведём — чтобы не плодить копии. Пример: [`../auth-service/README.md`](../auth-service/README.md). Обзор репозитория: [`../README.md`](../README.md).

## С чего начать

| Документ | Назначение |
|----------|------------|
| [architecture.md](architecture.md) | Контейнеры, потоки данных, RabbitMQ, Mermaid-диаграммы |
| [implementation-scope.md](implementation-scope.md) | Перечень реализованных возможностей и ссылки в код |
| [glossary.md](glossary.md) | Термины домена и инфраструктуры |
| [requirements/case-drivee.md](requirements/case-drivee.md) | Резюме кейса Drivee (после переноса из DOCX) |
| [operations/local-run.md](operations/local-run.md) | Локальный запуск через Docker Compose |
| [frontend/nl-chat-and-reports.md](frontend/nl-chat-and-reports.md) | NL-чат: WS BFF, удаление хвоста, id user/assistant, лента, модалка отчёта, тулбар |
| [frontend/websocket-client.md](frontend/websocket-client.md) | Клиент: WsClient, `useWsStore` / `useWsEvent`, жизненный цикл, формат `{ type, payload }` |

## Сервисы и приложения

| Папка | Исходники |
|-------|-----------|
| [auth-service/](auth-service/README.md) | [`../auth-service/`](../auth-service/) |
| [bff-service/](bff-service/README.md) | [`../bff-service/`](../bff-service/) |
| [analytics-service/](analytics-service/README.md) | [`../analytics-service/`](../analytics-service/) |
| [report-task-service/](report-task-service/README.md) | [`../report-task-service/`](../report-task-service/) |
| [sql-generator-worker/](sql-generator-worker/README.md) | [`../sql-generator-worker/`](../sql-generator-worker/) |
| [nl-orchestrator-worker/](nl-orchestrator-worker/README.md) | [`../nl-orchestrator-worker/`](../nl-orchestrator-worker/) |
| [notification-service/](notification-service/README.md) | [`../notification-service/`](../notification-service/) |
| [frontend/](frontend/README.md) | [`../frontend/`](../frontend/) |

## Инфраструктура и скрипты

| Документ | Содержание |
|----------|------------|
| [infrastructure/README.md](infrastructure/README.md) | Обзор слоя инфраструктуры |
| [infrastructure/databases.md](infrastructure/databases.md) | Две PostgreSQL, bootstrap, сиды |
| [infrastructure/messaging.md](infrastructure/messaging.md) | RabbitMQ: очереди и участники |
| [infrastructure/edge.md](infrastructure/edge.md) | Nginx, CloudPub, Redis |

## Как поддерживать

При изменении контрактов API, очередей или портов обновляйте соответствующий раздел в `docs/<сервис>/` и при необходимости [architecture.md](architecture.md) и [implementation-scope.md](implementation-scope.md).
