# nl-orchestrator-worker — ключевые файлы

Относительно [`nl-orchestrator-worker/`](../../nl-orchestrator-worker/).

| Путь | Роль |
|------|------|
| `Dockerfile` | Образ. |
| `app/worker_main.py` | Главный цикл и обработка всех типов MQ-сообщений. |
| `app/core/config.py` | Конфигурация. |
| `app/core/queues.py` | Имена очередей. |
| `app/services/chat_llm.py` | LLM-слой чата. |
| `app/schemas/analytics.py` | Схемы данных. |
