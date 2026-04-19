"""
ML / SQL generator worker: очередь nl_sql_generate_request → LLM → guardrails → SELECT → результат в nl_sql_jobs и nl_sql_generate_result.
"""
from __future__ import annotations

import asyncio
import json
import logging
import uuid

import pika
from sqlalchemy import create_engine

from app.core.config import get_settings
from app.core.queues import QUEUE_GENERATE_REQUEST, QUEUE_GENERATE_RESULT
from app.schemas.analytics import TableSchema
from app.services.chart_builder import build_chart
from app.services.job_db import update_job_row
from app.services.llm_service import generate_sql
from app.services.query_executor import execute_select
from app.services.sql_guard import allowed_table_set, validate_and_prepare_sql

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sql_generator_worker")

_engine_cache = None


def get_data_engine():
    global _engine_cache
    if _engine_cache is None:
        _engine_cache = create_engine(
            get_settings().ANALYTICS_DATABASE_URL, pool_pre_ping=True
        )
    return _engine_cache


async def run_pipeline(payload: dict) -> dict:
    settings = get_settings()
    job_id = uuid.UUID(payload["job_id"])
    user_id = payload["user_id"]
    question = payload["question"]
    tables = [TableSchema.model_validate(t) for t in payload["schema_tables"]]

    update_job_row(job_id, status="processing")

    try:
        raw_sql, explanation, _excerpt = await generate_sql(question, tables)
        allowed = allowed_table_set()
        sql, guard_warnings = validate_and_prepare_sql(
            raw_sql,
            settings.QUERY_MAX_ROWS,
            allowed,
        )
        cols, rows = execute_select(
            get_data_engine(),
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

        update_job_row(
            job_id,
            status="done",
            sql=sql,
            explanation=explanation,
            result_payload=result_payload,
        )

        return {
            "job_id": str(job_id),
            "user_id": user_id,
            "status": "done",
            "question": question,
            **result_payload,
            "error": None,
        }
    except Exception as e:
        logger.exception("pipeline failed")
        err = str(e)
        update_job_row(job_id, status="error", error=err)
        return {
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
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_GENERATE_REQUEST, durable=True)
    channel.queue_declare(queue=QUEUE_GENERATE_RESULT, durable=True)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=QUEUE_GENERATE_REQUEST, on_message_callback=on_message)
    logger.info("Worker listening on %s", QUEUE_GENERATE_REQUEST)
    channel.start_consuming()


if __name__ == "__main__":
    main()
