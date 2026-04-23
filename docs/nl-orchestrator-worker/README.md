# nl-orchestrator-worker

## Зачем нужен

**Оркестрация NL-диалога:** потребляет входящие сообщения чата из **`nl_chat_incoming`**, обращается к LLM и к **analytics-service** / **auth-service** по HTTP, ставит задачи в **`nl_sql_generate_request`**, читает **`nl_sql_generate_result_chat`**, публикует ответы в **`nl_chat_out`**. Обрабатывает очередь **`report_task_incoming_v1`** для сценариев отчётов.

## Границы

- Не заменяет BFF: клиент ходит в BFF, BFF в MQ; этот воркер — серверная логика «мозга» чата.
- Использует внутренние токены (`INTERNAL_NL_CHAT_SYNC_TOKEN`, `REPORT_TASK_INTERNAL_TOKEN`) при вызовах upstream.

## Зависимости

- RabbitMQ, analytics-service, auth-service, notification-service (URL в env), report-task-service.

## Исходники

[`../../nl-orchestrator-worker/`](../../nl-orchestrator-worker/).

Детали: [architecture.md](architecture.md), [modules.md](modules.md), [files.md](files.md).
