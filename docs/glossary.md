# Глоссарий

Термины, которые встречаются в коде и документации. При появлении отдельного описания кейса (см. [requirements/case-drivee.md](requirements/case-drivee.md)) сюда можно добавить формулировки заказчика. Актуальный перечень возможностей в репозитории: [implementation-scope.md](implementation-scope.md).

## Продукт и домен

| Термин | Описание |
|--------|----------|
| **Drivee / кейс** | Бизнес-сценарий соревнования; детали — в `requirements/case-drivee.md`, когда текст ТЗ будет перенесён в репозиторий. |
| **Заказы (warehouse)** | Аналитические данные в `main_db`, таблица в духе `drivee_orders` (см. bootstrap и [infrastructure/databases.md](infrastructure/databases.md)). |

## Архитектура

| Термин | Описание |
|--------|----------|
| **BFF** | Backend-for-frontend: единая HTTP/WebSocket точка для клиента, прокси к микросервисам. |
| **Platform DB** | PostgreSQL `postgres-db`: пользователи, чаты, метаданные платформы. |
| **Main DB / warehouse** | PostgreSQL `main-db`: данные для аналитики и NL→SQL по кейсу. |
| **Источник данных (analytics source)** | Именованный DSN к БД; в compose задаётся через `ANALYTICS_SOURCES_INLINE` и связанные переменные. |
| **NL-чат** | Диалог на естественном языке с генерацией SQL и ответов; цепочка BFF → RabbitMQ → nl-orchestrator-worker → analytics / sql-generator-worker. |

## Технические

| Термин | Описание |
|--------|----------|
| **JWT** | Токен доступа после логина; BFF валидирует и прокидывает `X-User-Id`, `X-User-Role` во внутренние вызовы. |
| **Internal token** | Секреты вроде `INTERNAL_NL_CHAT_SYNC_TOKEN`, `REPORT_TASK_INTERNAL_TOKEN` для вызовов между сервисами. |
