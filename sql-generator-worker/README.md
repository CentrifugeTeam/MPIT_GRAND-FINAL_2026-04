# SQL generator worker

Фоновый воркер генерации и выполнения SQL: читает **`nl_sql_generate_request`**, вызывает LLM при необходимости, валидирует запросы к warehouse, публикует результат в **`nl_sql_generate_result`** (BFF/UI) и **`nl_sql_generate_result_chat`** (nl-orchestrator-worker для чата).

Публичного HTTP API в типичном compose-развёртывании нет — только RabbitMQ и подключения к БД.

## Переменные окружения

См. `app/core/config.py`: URL БД, RabbitMQ, LLM, лимиты и guardrails SQL.

## Документация

Архитектура, модули, очереди: [docs/sql-generator-worker/README.md](../docs/sql-generator-worker/README.md).
