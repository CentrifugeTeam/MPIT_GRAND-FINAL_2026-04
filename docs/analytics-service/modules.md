# analytics-service — модули

| Путь | Назначение |
|------|------------|
| `app/main.py` | FastAPI, lifespan, роутеры. |
| `app/core/config.py` | DSN, LLM, лимиты запросов, токены внутренних вызовов. |
| `app/core/queues.py` | Имена очередей RabbitMQ. |
| `app/middleware/request_audit.py` | Аудит запросов. |
| `app/api/analytics.py` | Схема, interpret, чаты, история, задачи NL/SQL. |
| `app/api/data_sources.py` | CRUD источников данных (ключ → DSN). |
| `app/api/access_policies.py` | Политики доступа по роли. |
| `app/schemas/analytics.py` | Pydantic-модели ответов. |
| `app/db/platform_*` | ORM база платформы (модели, сессия). |
| `app/services/analytics_db.py` | Выполнение read-only SQL на warehouse. |
| `app/services/db_schema.py` | Интроспекция схемы. |
| `app/services/schema_cache.py` | Кэш схемы в памяти/БД. |
| `app/services/schema_scheduler.py` | Фоновое обновление схемы. |
| `app/services/chat_store.py` | Сообщения чатов на платформе. |
| `app/services/history_unified.py` | История запросов пользователя. |
| `app/services/job_store.py` | Задачи генерации SQL. |
| `app/services/rabbitmq_publish.py` | Обёртка publish в RabbitMQ (использование по сценариям; постановка `nl_sql_generate_request` — у оркестратора). |
| `app/services/question_interpretation.py` | NL → черновик намерения (LLM). |
| `app/services/query_quality_llm.py` | Оценка/улучшение качества SQL (LLM). |
| `app/services/data_sources_store.py` | Хранение конфигурации источников. |
| `app/services/access_policy.py` | Проверка политик. |
| `app/services/access_policy_store.py` | CRUD политик в БД. |
| `app/services/sensitive_redaction.py` | Маскирование чувствительных полей. |
| `app/services/metrics_glossary.py` | Справочники метрик для подсказок. |
