# nl-orchestrator-worker — модули

| Путь | Назначение |
|------|------------|
| `app/worker_main.py` | Подключение к RabbitMQ (aio-pika), обработчики сообщений чата и отчётов, публикация исходящих событий. |
| `app/core/config.py` | URL сервисов, LLM, лимиты истории, порог confidence. |
| `app/core/queues.py` | Константы имён очередей. |
| `app/services/chat_llm.py` | Промпты и вызовы LLM для шага диалога. |
| `app/schemas/analytics.py` | DTO для обмена с analytics API. |
