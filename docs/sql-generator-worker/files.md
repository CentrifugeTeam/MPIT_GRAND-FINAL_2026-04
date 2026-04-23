# sql-generator-worker — ключевые файлы

Относительно [`sql-generator-worker/`](../../sql-generator-worker/).

| Путь | Роль |
|------|------|
| `Dockerfile` | Образ воркера. |
| `app/worker_main.py` | Consumer + бизнес-поток. |
| `app/core/config.py` | Env. |
| `app/core/queues.py` | Очереди. |
| `app/services/query_executor.py` | Выполнение SQL. |
| `app/services/sql_guard.py` | Guardrails. |
| `app/services/llm_service.py` | LLM. |
| `app/services/job_db.py` | Персистентность задачи. |
