# MPIT Grand Final — платформа аналитики и NL→SQL

Монорепозиторий кейса **Drivee (MPIT)**: микросервисный backend с BFF, отдельным фронтендом на React, двумя базами PostgreSQL, RabbitMQ для чат-оркестрации и SQL-воркера, опционально Redis (rate limit) и LLM для интерпретации запросов и генерации SQL.

## Документация

| Раздел | Описание |
|--------|----------|
| [docs/README.md](docs/README.md) | Оглавление и ссылки на описание каждого сервиса |
| [docs/architecture.md](docs/architecture.md) | Архитектура всего решения и диаграммы Mermaid |
| [docs/implementation-scope.md](docs/implementation-scope.md) | Перечень реализованных возможностей и ссылки в код |
| [docs/requirements/case-drivee.md](docs/requirements/case-drivee.md) | Место под текст кейса из ТЗ |
| [docs/operations/local-run.md](docs/operations/local-run.md) | Локальный запуск через Docker Compose |

Структура **по сервисам**: каталоги `docs/auth-service/`, `docs/bff-service/`, … — в каждом `README.md`, `architecture.md`, `modules.md`, `files.md`. У каждого сервиса в дереве кода (`bff-service/`, `nl-orchestrator-worker/` и т.д.) — краткий **`README.md`** у корня каталога со ссылкой в `docs/`.

## Быстрый старт

1. Скопируйте [`.example.env`](.example.env) в `.env` и задайте как минимум `LLM_API_KEY` (и при необходимости `CLOUDPUB_TOKEN`).
2. Из корня репозитория (рядом с этим файлом и `docker-compose.yml`):

```bash
docker compose up --build
```

3. Дождитесь healthy для БД и RabbitMQ и успешного завершения `main-db-bootstrap`.
4. Откройте фронтенд на [http://localhost:5173](http://localhost:5173) или API BFF на [http://localhost:8000/docs](http://localhost:8000/docs).

Подробности портов и сервисов: [docs/operations/local-run.md](docs/operations/local-run.md).

## Репозиторий

Основные каталоги: `bff-service`, `auth-service`, `analytics-service`, `report-task-service`, `sql-generator-worker`, `nl-orchestrator-worker`, `notification-service`, `frontend`, `infrastructure`, `scripts`.
