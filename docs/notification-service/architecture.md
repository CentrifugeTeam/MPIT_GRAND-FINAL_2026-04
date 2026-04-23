# notification-service — внутренняя архитектура

```mermaid
flowchart LR
    subgraph api [API container]
        FAST["FastAPI main"]
        APIR["api/notifications"]
        CRUD["crud + models"]
        RAB["rabbitmq_service publish"]
    end
    subgraph worker [Worker container]
        EW["email_worker.py"]
        ES["email_service SMTP"]
    end
    DB[(postgres-db)]
    Q[["email_queue"]]
    FAST --> APIR
    APIR --> CRUD
    APIR --> RAB
    CRUD --> DB
    RAB --> Q
    Q --> EW
    EW --> ES
```

`worker.py` в репозитории может дублировать или дополнять логику воркера — актуальную точку входа для compose смотрите в [`docker-compose.yml`](../../docker-compose.yml).
