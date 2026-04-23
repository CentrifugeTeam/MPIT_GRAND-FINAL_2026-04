# sql-generator-worker — модули

| Путь | Назначение |
|------|------------|
| `app/worker_main.py` | Точка входа, цикл consumer, маршрутизация сообщений, публикация результатов. |
| `app/core/config.py` | DSN, LLM, лимиты строк/байтов, таймауты EXPLAIN. |
| `app/core/queues.py` | Имена очередей. |
| `app/schemas/analytics.py` | Структуры payload задач/результатов. |
| `app/services/llm_service.py` | Вызовы LLM для генерации SQL. |
| `app/services/sql_guard.py` | Ограничения и проверки SQL. |
| `app/services/query_executor.py` | Выполнение и сбор результата. |
| `app/services/chart_builder.py` | Построение данных для графиков. |
| `app/services/job_db.py` | Обновление статуса job в БД. |
| `app/services/analytics_source_resolve.py` | Выбор DSN по ключу источника. |
