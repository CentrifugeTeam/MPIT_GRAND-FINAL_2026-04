"""
ML / SQL generator worker: очередь nl_sql_generate_request → LLM (только SQL) → guardrails → SELECT → результат.
При наличии conversation_id дублирует результат в nl_sql_generate_result_chat для nl-orchestrator-worker.
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid

import pika
from sqlalchemy import create_engine

from app.core.config import get_settings
from app.core.queues import (
    QUEUE_GENERATE_REQUEST,
    QUEUE_GENERATE_RESULT,
    QUEUE_GENERATE_RESULT_CHAT,
)
from app.schemas.analytics import TableSchema
from app.services.chart_builder import build_chart
from app.services.job_db import update_job_row
from app.services.llm_service import generate_sql
from app.services.analytics_source_resolve import resolve_analytics_database_url
from app.services.query_executor import execute_select
from app.services.sql_guard import allowed_table_set, validate_and_prepare_sql

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sql_generator_worker")

_engine_by_url: dict[str, object] = {}
_RABBIT_CONNECT_RETRY_BASE_SEC = 1.0
_RABBIT_CONNECT_RETRY_MAX_SEC = 15.0


def get_data_engine_for_url(url: str):
    global _engine_by_url
    if url not in _engine_by_url:
        _engine_by_url[url] = create_engine(url, pool_pre_ping=True)
    return _engine_by_url[url]


def _is_chat_job(payload: dict) -> bool:
    return bool(payload.get("conversation_id"))


async def run_pipeline(payload: dict) -> dict:
    settings = get_settings()
    raw_sk = payload.get("analytics_source_key")
    sk = raw_sk.strip() if isinstance(raw_sk, str) else None
    if sk == "":
        sk = None
    db_url = resolve_analytics_database_url(sk)
    data_engine = get_data_engine_for_url(db_url)

    job_id = uuid.UUID(payload["job_id"])
    user_id = payload["user_id"]
    question = payload["question"]
    tables = [TableSchema.model_validate(t) for t in payload["schema_tables"]]
    chat_job = _is_chat_job(payload)
    hints = payload.get("orchestrator_hints")
    hints_str = hints if isinstance(hints, str) else None

    if not chat_job:
        update_job_row(job_id, status="processing")

    try:
        gctx = payload.get("glossary_context")
        raw_sql, explanation, _excerpt = await generate_sql(
            question,
            tables,
            glossary_context=gctx if isinstance(gctx, str) else None,
            orchestrator_hints=hints_str,
        )
        allowed = allowed_table_set()
        mr = payload.get("max_rows")
        max_rows = int(mr) if mr is not None else None
        sql, guard_warnings = validate_and_prepare_sql(
            raw_sql,
            max_rows,
            allowed,
            schema_tables=tables,
        )
        cols, rows = execute_select(
            data_engine,
            sql,
            timeout_ms=settings.QUERY_TIMEOUT_MS,
        )
        chart_spec, chart_payload = build_chart(cols, rows)

        result_payload = {
            "question": question,
            "sql": sql,
            "explanation": explanation,
            "columns": cols,
            "rows": rows,
            "row_count": len(rows),
            "chart": chart_spec.model_dump(),
            "chart_payload": chart_payload,
            "guard_warnings": guard_warnings,
        }
        interp_in = payload.get("interpretation")
        if isinstance(interp_in, dict):
            result_payload["interpretation"] = interp_in

        if not chat_job:
            update_job_row(
                job_id,
                status="done",
                sql=sql,
                explanation=explanation,
                result_payload=result_payload,
            )

        out: dict = {
            "job_id": str(job_id),
            "user_id": user_id,
            "status": "done",
            "question": question,
            **result_payload,
            "error": None,
        }
        if chat_job:
            out["conversation_id"] = str(payload["conversation_id"])
            if payload.get("sql_turn_id"):
                out["sql_turn_id"] = str(payload["sql_turn_id"])
        return out
    except Exception as e:
        logger.exception("pipeline failed")
        err = str(e)
        if not chat_job:
            update_job_row(job_id, status="error", error=err)
        err_out: dict = {
            "job_id": str(job_id),
            "user_id": user_id,
            "status": "error",
            "question": question,
            "error": err,
            "sql": None,
            "explanation": None,
            "columns": [],
            "rows": [],
            "row_count": 0,
            "chart": {"type": "table"},
            "chart_payload": {},
            "guard_warnings": [],
        }
        interp_in = payload.get("interpretation")
        if isinstance(interp_in, dict):
            err_out["interpretation"] = interp_in
        if chat_job:
            err_out["conversation_id"] = str(payload["conversation_id"])
            if payload.get("sql_turn_id"):
                err_out["sql_turn_id"] = str(payload["sql_turn_id"])
        return err_out


def on_message(ch, method, properties, body: bytes) -> None:
    try:
        payload = json.loads(body.decode("utf-8"))
        logger.info("received job %s", payload.get("job_id"))
        result = asyncio.run(run_pipeline(payload))
        out = json.dumps(result, default=str).encode("utf-8")
        ch.basic_publish(
            exchange="",
            routing_key=QUEUE_GENERATE_RESULT,
            body=out,
            properties=pika.BasicProperties(delivery_mode=2),
        )
        if payload.get("conversation_id"):
            ch.queue_declare(queue=QUEUE_GENERATE_RESULT_CHAT, durable=True)
            ch.basic_publish(
                exchange="",
                routing_key=QUEUE_GENERATE_RESULT_CHAT,
                body=out,
                properties=pika.BasicProperties(delivery_mode=2),
            )
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception:
        logger.exception("on_message")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def main() -> None:
    s = get_settings()
    url = (
        f"amqp://{s.RABBITMQ_USER}:{s.RABBITMQ_PASSWORD}"
        f"@{s.RABBITMQ_HOST}:{s.RABBITMQ_PORT}/"
    )
    params = pika.URLParameters(url)
    delay = _RABBIT_CONNECT_RETRY_BASE_SEC
    while True:
        try:
            connection = pika.BlockingConnection(params)
            break
        except Exception as e:
            logger.warning(
                "RabbitMQ connect failed (%s). Retrying in %.1fs", e, delay
            )
            time.sleep(delay)
            delay = min(delay * 2, _RABBIT_CONNECT_RETRY_MAX_SEC)
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_GENERATE_REQUEST, durable=True)
    channel.queue_declare(queue=QUEUE_GENERATE_RESULT, durable=True)
    channel.queue_declare(queue=QUEUE_GENERATE_RESULT_CHAT, durable=True)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=QUEUE_GENERATE_REQUEST, on_message_callback=on_message)
    logger.info("Worker listening on %s", QUEUE_GENERATE_REQUEST)
    channel.start_consuming()


if __name__ == "__main__":
    main()
