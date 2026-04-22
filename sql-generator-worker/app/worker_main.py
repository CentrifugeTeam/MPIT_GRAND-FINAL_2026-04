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
from app.services.query_executor import execute_select, explain_total_cost
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


def _write_audit_row(
    *,
    user_id: str,
    user_role: str | None,
    source_key: str | None,
    question: str,
    sql_text: str | None,
    status: str,
    guard_error: str | None,
    planner_cost: float | None,
    duration_ms: int | None,
) -> None:
    s = get_settings()
    if not getattr(s, "QUERY_AUDIT_ENABLED", True):
        return
    url = getattr(s, "PLATFORM_DATABASE_URL", None) or getattr(
        s, "ANALYTICS_DATABASE_URL", ""
    )
    if not url or not str(url).strip():
        return
    try:
        eng = get_data_engine_for_url(str(url))
        from sqlalchemy import text as sa_text

        with eng.begin() as conn:
            conn.execute(
                sa_text(
                    """
                    INSERT INTO nl_query_audit (
                        id, user_id, user_role, source_key, question_redacted,
                        sql_text, status, guard_error, planner_cost, duration_ms
                    ) VALUES (
                        CAST(:id AS uuid), :uid, :role, :sk, :q, :sqlt, :st, :ge, :pc, :dm
                    )
                    """
                ),
                {
                    "id": str(uuid.uuid4()),
                    "uid": str(user_id)[:64],
                    "role": (user_role or "")[:64],
                    "sk": (source_key or "")[:64],
                    "q": (question or "")[:4000],
                    "sqlt": (sql_text or "")[:8000] if sql_text else None,
                    "st": status[:32],
                    "ge": (guard_error or "")[:2000] if guard_error else None,
                    "pc": planner_cost,
                    "dm": duration_ms,
                },
            )
    except Exception:
        logger.warning("audit insert failed", exc_info=True)


async def run_pipeline(payload: dict) -> dict:
    settings = get_settings()
    raw_sk = payload.get("analytics_source_key")
    sk = raw_sk.strip() if isinstance(raw_sk, str) else None
    if sk == "":
        sk = None
    db_url = resolve_analytics_database_url(sk)
    data_engine = get_data_engine_for_url(db_url)

    import time as time_mod

    t0 = time_mod.monotonic()
    job_id = uuid.UUID(payload["job_id"])
    user_id = payload["user_id"]
    user_role = payload.get("user_role")
    if isinstance(user_role, str):
        user_role = user_role.strip().upper()
    else:
        user_role = None
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
        cap = int(getattr(settings, "GLOBAL_MAX_ROWS", 100_000) or 100_000)
        if max_rows is not None:
            max_rows = min(max_rows, cap)
        else:
            max_rows = cap
        ap = payload.get("access_policy")
        access_policy = ap if isinstance(ap, dict) else None
        sql, guard_warnings = validate_and_prepare_sql(
            raw_sql,
            max_rows,
            allowed,
            schema_tables=tables,
            access_policy=access_policy,
        )
        cost_cap = float(getattr(settings, "MAX_PLANNER_TOTAL_COST", 0) or 0)
        planner_cost: float | None = None
        if cost_cap > 0:
            eto = int(getattr(settings, "EXPLAIN_TIMEOUT_MS", 5000) or 5000)
            planner_cost = explain_total_cost(data_engine, sql, eto)
            if planner_cost is not None and planner_cost > cost_cap:
                raise ValueError(
                    f"Оценка стоимости плана ({planner_cost:.1f}) превышает лимит {cost_cap:.1f}"
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
        dt_ms = int((time_mod.monotonic() - t0) * 1000)
        _write_audit_row(
            user_id=str(user_id),
            user_role=user_role,
            source_key=sk,
            question=str(question)[:2000],
            sql_text=sql,
            status="done",
            guard_error=None,
            planner_cost=planner_cost,
            duration_ms=dt_ms,
        )
        return out
    except Exception as e:
        logger.exception("pipeline failed")
        err = str(e)
        try:
            dt_ms = int((time_mod.monotonic() - t0) * 1000)
            _write_audit_row(
                user_id=str(user_id),
                user_role=user_role,
                source_key=sk,
                question=str(question)[:2000],
                sql_text=None,
                status="error",
                guard_error=err[:2000],
                planner_cost=None,
                duration_ms=dt_ms,
            )
        except Exception:
            pass
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
