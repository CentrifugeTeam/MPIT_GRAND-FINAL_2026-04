# RabbitMQ

- **Образ:** `rabbitmq:3.12-management`
- **Порты:** `5672` (AMQP), `15672` (management UI)
- **Учётные данные по умолчанию:** `admin` / `admin123` (см. compose)

Очереди **durable**; имена заданы константами в коде (`app/core/queues.py` в соответствующих сервисах).

## Очереди NL→SQL и чата

| Имя очереди | Константа в коде | Кто публикует | Кто потребляет |
|-------------|------------------|---------------|----------------|
| `nl_sql_generate_request` | `QUEUE_GENERATE_REQUEST` | nl-orchestrator-worker | sql-generator-worker |
| `nl_sql_generate_result` | `QUEUE_GENERATE_RESULT` | sql-generator-worker | BFF (`analytics_mq_consumer`) |
| `nl_sql_generate_result_chat` | `QUEUE_GENERATE_RESULT_CHAT` | sql-generator-worker | nl-orchestrator-worker |
| `nl_chat_incoming` | `QUEUE_CHAT_INCOMING` | BFF (`chat_mq`) | nl-orchestrator-worker |
| `nl_chat_out` | `QUEUE_CHAT_OUT` | nl-orchestrator-worker | BFF (`chat_mq`) |

## Отчёты

| Имя очереди | Константа | Кто публикует | Кто потребляет |
|-------------|-----------|---------------|----------------|
| `report_task_incoming_v1` | `QUEUE_REPORT_TASK_INCOMING` / `QUEUE_REPORT_TASK_INCOMING_V1` | report-task-service | nl-orchestrator-worker |

## Уведомления по email

| Имя очереди | Кто публикует | Кто потребляет |
|-------------|---------------|----------------|
| `email_queue` | notification-service API (`rabbitmq_service`) | notification-worker (`email_worker.py`) |

Диаграмма взаимодействий: [../architecture.md](../architecture.md).
