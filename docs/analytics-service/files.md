# analytics-service — ключевые файлы

Относительно [`analytics-service/`](../../analytics-service/).

| Путь | Роль |
|------|------|
| `Dockerfile` | Образ сервиса. |
| `app/main.py` | Роутинг и lifecycle. |
| `app/core/config.py` | Конфигурация. |
| `app/core/queues.py` | Очереди MQ. |
| `app/api/analytics.py` | Основной объём REST NL/SQL. |
| `app/api/data_sources.py` | Источники данных. |
| `app/api/access_policies.py` | Политики ADMIN. |
| `app/services/rabbitmq_publish.py` | Отправка задач воркеру. |
| `app/services/schema_cache.py` / `schema_scheduler.py` | Схема БД. |
| `app/services/job_store.py` | Жизненный цикл job генерации. |
| `app/db/platform_models.py` | Модели платформенной БД. |
| `app/middleware/request_audit.py` | Аудит. |
