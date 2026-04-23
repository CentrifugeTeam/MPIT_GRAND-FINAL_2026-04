# report-task-service — внутренняя архитектура

```mermaid
flowchart LR
    API["FastAPI /api/tasks"]
    TS["task_store / run_store"]
    SCH["scheduler + schedule"]
    MQ["rabbitmq_publish"]
    DB[(postgres-db)]
    Q[[report_task_incoming_v1]]
    API --> TS
    API --> SCH
    SCH --> MQ
    TS --> DB
    MQ --> Q
```

- **scheduler** периодически (`DISPATCH_INTERVAL_SECONDS`) выбирает задачи и публикует прогон в RabbitMQ.
- **enqueue_task_run** вызывается из API при ручном запуске или из планировщика.
