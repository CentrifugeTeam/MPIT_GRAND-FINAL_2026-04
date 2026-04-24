# nl-orchestrator-worker — ключевые файлы

Относительно [`nl-orchestrator-worker/`](../../nl-orchestrator-worker/).

| Путь | Роль |
|------|------|
| `Dockerfile` | Образ. |
| `app/worker_main.py` | Главный цикл MQ; **раздельные** id: пользователь `message_id`, ответ `assistant_message_id` (`PendingCtx`). См. [../frontend/nl-chat-and-reports.md](../frontend/nl-chat-and-reports.md). |
| `app/core/config.py` | Конфигурация. |
| `app/core/queues.py` | Имена очередей. |
| `app/services/chat_llm.py` | LLM-слой чата. |
| `app/schemas/analytics.py` | Схемы данных. |
