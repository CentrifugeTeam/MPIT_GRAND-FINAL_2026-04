"""Имена очередей RabbitMQ (общие для analytics, worker, bff, orchestrator)."""

QUEUE_GENERATE_REQUEST = "nl_sql_generate_request"
QUEUE_GENERATE_RESULT = "nl_sql_generate_result"

# Чат с NL-оркестратором (BFF ↔ nl-orchestrator-worker)
QUEUE_CHAT_INCOMING = "nl_chat_incoming"
QUEUE_CHAT_OUT = "nl_chat_out"

# Результат SQL только для оркестратора (не забирает BFF nl_sql consumer)
QUEUE_GENERATE_RESULT_CHAT = "nl_sql_generate_result_chat"
