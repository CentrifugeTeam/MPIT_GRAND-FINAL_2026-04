# MPIT Grand Final — платформа NL→SQL и аналитики (кейс Drivee)

Пользователь задаёт вопрос на естественном языке; система строит SQL с учётом схемы и политик, выполняет запрос и возвращает таблицу и графики; есть отчёты по расписанию, уведомления и совместные NL-чаты.

Монорепозиторий: **BFF** (HTTP, WebSocket, SSE), микросервисы **auth**, **analytics**, **report-task**, **notification**, воркеры **nl-orchestrator** и **sql-generator**, **React (Vite)** на фронте, две **PostgreSQL** (платформа и витрина), **RabbitMQ**, опционально **Redis**.

## Куда смотреть дальше

Вся подробная документация собрана в каталоге **[`docs/`](docs/README.md)** — начните с оглавления там.

| Если нужно… | Документ |
|-------------|----------|
| Запустить локально, порты, `dataset/train.csv`, `.env` | [`docs/operations/local-run.md`](docs/operations/local-run.md) |
| Контейнеры, очереди, Mermaid-флоу NL→SQL, SSE, отчёты | [`docs/architecture.md`](docs/architecture.md) |
| Что реализовано и ссылки в код | [`docs/implementation-scope.md`](docs/implementation-scope.md) |
| Термины (BFF, очереди, guardrails, SSE…) | [`docs/glossary.md`](docs/glossary.md) |
| Кейс Drivee и экспертное сопоставление с ТЗ | [`docs/requirements/case-drivee.md`](docs/requirements/case-drivee.md), [`docs/requirements/EXPERT_REVIEW_DRIVEE.md`](docs/requirements/EXPERT_REVIEW_DRIVEE.md) |
| NL-чат, WS, отчёты, PDF, шаринг | [`docs/frontend/nl-chat-and-reports.md`](docs/frontend/nl-chat-and-reports.md) |

По каждому сервису в **`docs/<имя-сервис>/`** есть краткий `README.md` (роль, порты, границы); в дереве кода у сервиса — только короткий `README.md` со ссылкой в `docs/`.

## Быстрый старт

Инструкция по запуску, данным `dataset/train.csv`, переменным окружения и URL: **[`docs/operations/local-run.md`](docs/operations/local-run.md)**.

## Репозиторий (каталоги верхнего уровня)

`bff-service`, `auth-service`, `analytics-service`, `report-task-service`, `sql-generator-worker`, `nl-orchestrator-worker`, `notification-service`, `frontend`, `infrastructure`, `scripts`, `docs`, `dataset`.
