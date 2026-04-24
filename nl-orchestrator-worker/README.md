# NL orchestrator worker

Оркестрация **NL-диалога** и сценариев **отчётов**: потребляет **`nl_chat_incoming`**, обращается к LLM и к **analytics-service** / **auth-service**, ставит задачи в **`nl_sql_generate_request`**, читает **`nl_sql_generate_result_chat`**, публикует ответы в **`nl_chat_out`**. Очередь **`report_task_incoming_v1`** — прогоны отчётов.

Клиент ходит в BFF; этот воркер — серверная логика «мозга» чата и связки с отчётами (внутренние токены `INTERNAL_NL_CHAT_SYNC_TOKEN`, `REPORT_TASK_INTERNAL_TOKEN` при вызовах upstream).

## Переменные окружения

См. `app/core/config.py`: RabbitMQ, URL analytics/auth/notification/report-task, LLM, токены синхронизации чата.

## Документация

Архитектура, модули, очереди: [docs/nl-orchestrator-worker/README.md](../docs/nl-orchestrator-worker/README.md).
