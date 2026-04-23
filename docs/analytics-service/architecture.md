# analytics-service — внутренняя архитектура

## Поток данных

```mermaid
flowchart TB
    subgraph api [FastAPI]
        AR["analytics router"]
        DS["data_sources router"]
        AP["access_policies router"]
    end
    subgraph services [Сервисы]
        adb["analytics_db / db_schema"]
        hist["history_unified / chat_store"]
        interp["question_interpretation"]
        jobs["job_store internal nl-chat-sync"]
        pol["access_policy + access_policy_store"]
    end
    subgraph db [Хранилища]
        WH[(main_db warehouse)]
        PF[(postgres-db platform)]
    end
    AR --> adb
    AR --> hist
    AR --> interp
    AR --> jobs
    AP --> pol
    DS --> PF
    adb --> WH
    hist --> PF
    pol --> PF
    jobs -.->|"оркестратор публикует SQL job"| ExtOrch[nl-orchestrator-worker]
```

## Lifespan

- Инициализация таблиц платформы (`init_platform_tables`).
- Прогрев кэша схем (`refresh_schema_cache`).
- Планировщик обновления схем по cron-часу (`SCHEMA_CRON_HOUR`).

## Связь с воркером SQL

**nl-orchestrator-worker** после шага чата публикует JSON в **`nl_sql_generate_request`**. **sql-generator-worker** выполняет запрос и пишет результат в **`nl_sql_generate_result`** и **`nl_sql_generate_result_chat`**. Analytics держит согласованность через internal sync (токен в заголовке).
