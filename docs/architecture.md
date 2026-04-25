# Архитектура системы

Микросервисная платформа с **BFF** как единственной публичной точкой для клиента по **HTTP** (REST, **SSE** для уведомлений), **WebSocket** (NL-чат), **двумя PostgreSQL** (платформа и витрина данных), **RabbitMQ** для асинхронных сценариев NL→SQL, отчётов и email, **Redis** для rate limiting на BFF и для real-time ветки потока уведомлений (pub/sub при наличии Redis).

Термины: [glossary.md](glossary.md). Перечень модулей в коде: [implementation-scope.md](implementation-scope.md). Очереди и участники: [infrastructure/messaging.md](infrastructure/messaging.md). По сервисам: [README.md](README.md) и каталоги `docs/<сервис>/`.

## Диаграмма контейнеров

Обзорная карта: браузер обращается к фронту и к BFF (напрямую или через nginx). **SSE** обслуживается тем же **bff-service** по обычному HTTP. **Redis** связан с BFF (rate limit и канал обновлений для SSE).

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

Сводная последовательность. **Пошаговый разбор** — в разделе [NL-чат: детально](#nl-чат-детально) ниже.

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

Исходники: [nl-orchestrator-worker/app/worker_main.py](../nl-orchestrator-worker/app/worker_main.py), [bff-service/app/services/chat_mq.py](../bff-service/app/services/chat_mq.py), [bff-service/app/services/analytics_mq_consumer.py](../bff-service/app/services/analytics_mq_consumer.py).

## NL-чат: детально

### Фаза 1 — сообщение пользователя, схема, интерпретация, план и постановка SQL

```mermaid
sequenceDiagram
    participant FE as Frontend
    participant BFF as bff-service
    participant RMQ as RabbitMQ
    participant OR as nl-orchestrator-worker
    participant AN as analytics-service
    participant LLM as LLM_API
    FE->>BFF: WebSocket chat_message
    BFF->>RMQ: publish nl_chat_incoming
    RMQ->>OR: consume payload
    OR->>AN: HTTP GET schema по source_key и роли
    AN-->>OR: schema_tables JSON
    OR->>AN: HTTP POST interpret-question
    AN-->>OR: confidence warnings glossary_matches
    alt confidence ниже порога
        OR->>LLM: clarify_ambiguous_question
        LLM-->>OR: текст уточнения
        OR->>RMQ: publish nl_chat_out
        RMQ->>BFF: consume
        BFF->>FE: WebSocket assistant без SQL
    else confidence достаточен
        OR->>LLM: plan_turn schema glossary history
        LLM-->>OR: reasoning sql_question
        OR->>RMQ: publish nl_sql_generate_request
    end
```

### Фаза 2 — генерация SQL, guardrails, выполнение, синхрон истории, ответ в чат

```mermaid
sequenceDiagram
    participant RMQ as RabbitMQ
    participant SQL as sql-generator-worker
    participant LLM as LLM_API
    participant PgM as main-db
    participant OR as nl-orchestrator-worker
    participant AN as analytics-service
    participant BFF as bff-service
    participant FE as Frontend
    RMQ->>SQL: consume nl_sql_generate_request
    SQL->>LLM: генерация SQL по промпту и схеме
    LLM-->>SQL: текст SQL
    Note over SQL: sql_guard validate_and_prepare_sql
    SQL->>PgM: SELECT исполнение
    PgM-->>SQL: rows
    SQL->>RMQ: publish nl_sql_generate_result_chat
    SQL->>RMQ: publish nl_sql_generate_result
    RMQ->>OR: consume nl_sql_generate_result_chat
    OR->>AN: HTTP POST internal nl-chat-sync
    OR->>RMQ: publish nl_chat_out
    RMQ->>BFF: consume nl_chat_out
    BFF->>FE: WebSocket chat_assistant chart rows
    RMQ->>BFF: consume nl_sql_generate_result
    BFF->>FE: доставка в WS-сессию по job
```

Код: [sql-generator-worker/app/services/sql_guard.py](../sql-generator-worker/app/services/sql_guard.py), [sql-generator-worker/app/worker_main.py](../sql-generator-worker/app/worker_main.py).

## Интерпретация вопроса и ветка confidence

```mermaid
flowchart TD
    startNode([Сообщение пользователя в OR])
    startNode --> interpret[HTTP interpret-question в AN]
    interpret --> check{Порог confidence}
    check -->|ниже порога| clarify[LLM уточняющий ответ]
    clarify --> out1[nl_chat_out в BFF]
    check -->|не ниже порога| plan[LLM plan_turn]
    plan --> enqueue[publish nl_sql_generate_request]
    enqueue --> sqlPhase[Фаза 2 sql-generator-worker]
```

## Плановый отчёт (report task)

```mermaid
sequenceDiagram
    participant RP as report-task-service
    participant PgP as postgres-db
    participant RMQ as RabbitMQ
    participant OR as nl-orchestrator-worker
    participant AN as analytics-service
    participant SQL as sql-generator-worker
    RP->>PgP: чтение задач по расписанию APScheduler
    RP->>RMQ: publish report_task_incoming_v1
    Note over OR: payload conversation_id __report_run__
    RMQ->>OR: consume тот же контур что NL-чат
    OR->>AN: HTTP schema interpret при необходимости
    OR->>RMQ: nl_sql_generate_request
    RMQ->>SQL: consume и выполнение см фазу 2 NL-чата
```

## Уведомления в браузере (SSE)

```mermaid
sequenceDiagram
    participant FE as Frontend
    participant BFF as bff-service
    participant Redis as redis
    participant NT as notification-service
    participant PgP as postgres-db
    FE->>BFF: GET /api/notification/stream token query EventSource
    BFF->>NT: HTTP список уведомлений начальная выдача
    NT->>PgP: чтение записей
    PgP-->>NT: rows
    NT-->>BFF: JSON
    BFF-->>FE: SSE event notifications
    loop при наличии Redis pub/sub
        BFF->>Redis: subscribe stream channel user
        Redis-->>BFF: сообщение touch
        BFF->>NT: HTTP refresh списка
        NT->>PgP: чтение
        BFF-->>FE: SSE event notifications
    end
    Note over BFF,FE: без Redis BFF шлёт heartbeat и редкий poll к NT
```

Код: [bff-service/app/api/notification.py](../bff-service/app/api/notification.py), [bff-service/app/services/notification_realtime.py](../bff-service/app/services/notification_realtime.py).

## Email через очередь

```mermaid
sequenceDiagram
    participant NT as notification-service
    participant RMQ as RabbitMQ
    participant NW as notification-worker
    participant SMTP as SMTP
    NT->>RMQ: publish email_queue
    RMQ->>NW: consume
    NW->>SMTP: отправка письма
```

## Аутентификация (JWT)

```mermaid
sequenceDiagram
    participant FE as Frontend
    participant BFF as bff-service
    participant AU as auth-service
    participant PgP as postgres-db
    FE->>BFF: POST /api/auth/login
    BFF->>AU: POST /auth/login
    AU->>PgP: проверка пользователя
    PgP-->>AU: user row
    AU-->>BFF: access_token refresh_token
    BFF-->>FE: JWT клиенту
    Note over FE,BFF: далее REST и WS с Authorization Bearer
    Note over BFF,AN: BFF проксирует в Analytics Reports Notify с заголовками X-User-Id X-User-Role из JWT
```

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
