# Архитектура системы

Микросервисная платформа с **BFF** как единственной публичной HTTP/WebSocket точкой для фронтенда, **двумя PostgreSQL** (платформа и витрина данных), **RabbitMQ** для асинхронных сценариев NL→SQL, отчётов и email, **Redis** для опционального rate limiting на BFF.

Подробности по компонентам: [README.md](README.md) и папки `docs/<сервис>/`. Очереди: [infrastructure/messaging.md](infrastructure/messaging.md).

## Диаграмма контейнеров

```mermaid
flowchart TB
    subgraph client [Клиент]
        Browser[Browser]
    end
    subgraph edge [Край]
        Nginx[nginx:80]
        Frontend[frontend:Vite5173]
    end
    subgraph app [Приложение]
        BFF[bff-service:8000]
        Auth[auth-service:8002]
        Analytics[analytics-service:8009]
        Reports[report-task-service:8010]
        Notify[notification-service:8007]
    end
    subgraph workers [Воркеры]
        SqlGen[sql-generator-worker]
        NlOrch[nl-orchestrator-worker]
        NotifyW[notification-worker]
    end
    subgraph data [Данные]
        PgMain[(main-db)]
        PgPlat[(postgres-db)]
        Redis[(redis)]
    end
    subgraph mq [Очереди]
        RMQ[RabbitMQ]
    end
    Browser --> Nginx
    Browser --> Frontend
    Frontend --> BFF
    Nginx --> BFF
    BFF --> Auth
    BFF --> Analytics
    BFF --> Reports
    BFF --> Notify
    BFF --> RMQ
    BFF --> Redis
    Auth --> PgPlat
    Analytics --> PgMain
    Analytics --> PgPlat
    Analytics --> RMQ
    Reports --> PgPlat
    Reports --> RMQ
    Notify --> PgPlat
    Notify --> RMQ
    SqlGen --> RMQ
    SqlGen --> PgMain
    SqlGen --> PgPlat
    NlOrch --> RMQ
    NlOrch --> Analytics
    NlOrch --> Auth
    NotifyW --> RMQ
    NotifyW --> PgPlat
```

## Поток NL-чата (упрощённо)

```mermaid
sequenceDiagram
    participant FE as Frontend
    participant BFF as bff-service
    participant RMQ as RabbitMQ
    participant OR as nl-orchestrator-worker
    participant AN as analytics-service
    participant SQL as sql-generator-worker
    FE->>BFF: WebSocket chat_message
    BFF->>RMQ: publish nl_chat_incoming
    RMQ->>OR: consume
    OR->>AN: HTTP schema interpret jobs
    Note over OR,RMQ: nl-orchestrator публикует nl_sql_generate_request
    OR->>RMQ: publish nl_sql_generate_request
    RMQ->>SQL: consume
    SQL->>RMQ: publish nl_sql_generate_result_chat
    RMQ->>OR: consume
    OR->>RMQ: publish nl_chat_out
    RMQ->>BFF: consume nl_chat_out
    BFF->>FE: WebSocket events
    SQL->>RMQ: publish nl_sql_generate_result
    RMQ->>BFF: consumer to WS
    BFF->>FE: SQL result rows charts
```

На практике шаги и типы событий богаче (статусы, ошибки, reasoning); детали в [nl-orchestrator-worker/worker_main.py](../nl-orchestrator-worker/app/worker_main.py) и [bff-service/services](../bff-service/app/services/).

## Поток данных warehouse vs platform

```mermaid
flowchart LR
    CSV[dataset CSV]
    Boot[main-db-bootstrap]
    MainDb[(main-db drivee_orders)]
    Plat[(postgres-db)]
    Analytics[analytics-service]
    SqlW[sql-generator-worker]
    CSV --> Boot
    Boot --> MainDb
    Analytics --> MainDb
    Analytics --> Plat
    SqlW --> MainDb
    SqlW --> Plat
```

## Внешние зависимости

- **LLM API** (OpenAI-совместимый endpoint): analytics-service, sql-generator-worker, nl-orchestrator-worker — переменные `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL`.

## Дополнительно

- **CloudPub** публикует `nginx:80` наружу при заданном `CLOUDPUB_TOKEN` — см. [infrastructure/edge.md](infrastructure/edge.md).
