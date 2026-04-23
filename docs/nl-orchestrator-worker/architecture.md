# nl-orchestrator-worker — внутренняя архитектура

```mermaid
flowchart TB
    subgraph mq [RabbitMQ]
        QIN["nl_chat_incoming"]
        QREP["report_task_incoming_v1"]
        QSQL["nl_sql_generate_result_chat"]
        QOUT["nl_chat_out"]
        QREQ["nl_sql_generate_request"]
    end
    WM["worker_main asyncio"]
    LLM["chat_llm"]
    HTTP["httpx → analytics / auth / notification / report-task"]
    WM --> QIN
    WM --> QREP
    WM --> QSQL
    WM --> LLM
    WM --> HTTP
    WM --> QOUT
    WM --> QREQ
```

Основная логика сосредоточена в **`worker_main.py`** (обработка состояний, таймауты, маршрутизация типов сообщений). **`chat_llm.py`** инкапсулирует вызовы модели для черновика ответа и рассуждений.
