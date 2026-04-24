"""Потребление report_template_plan_request_v1 → LLM → bulk insert в report-task-service."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Optional

import aio_pika
import httpx
from sqlalchemy import text

from app.core.config import get_settings
from app.core.queues import QUEUE_REPORT_TEMPLATE_PLAN_REQUEST
from app.db.platform_session import platform_engine
from app.schemas.analytics import TableSchema
from app.services import schema_cache
from app.services.report_template_coverage import count_distinct_system_schedule_types
from app.services.report_template_plan_llm import (
    build_bulk_templates_payload,
    default_schedules_iso,
    generate_five_template_texts,
)
from app.services.schema_scheduler import refresh_schema_cache

logger = logging.getLogger(__name__)

_task: Optional[asyncio.Task] = None
_CONNECT_RETRY_BASE_SEC = 1.0
_CONNECT_RETRY_MAX_SEC = 15.0


async def _connect_with_retries(url: str) -> aio_pika.abc.AbstractRobustConnection:
    delay = _CONNECT_RETRY_BASE_SEC
    while True:
        try:
            return await aio_pika.connect_robust(url)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.warning("RabbitMQ connect failed (%s). Retrying in %.1fs", e, delay)
            await asyncio.sleep(delay)
            delay = min(delay * 2, _CONNECT_RETRY_MAX_SEC)


def _display_name_for_source(source_key: str) -> str:
    eng = platform_engine()
    try:
        with eng.connect() as conn:
            row = conn.execute(
                text(
                    "SELECT display_name FROM analytics_data_sources WHERE source_key = :k LIMIT 1"
                ),
                {"k": source_key.strip()},
            ).fetchone()
        if row and row[0]:
            return str(row[0])
    except Exception:
        logger.exception("report_template_consumer: display_name lookup failed")
    return source_key


def _tables_for_source(source_key: str) -> list[TableSchema]:
    s = get_settings()
    raw = schema_cache.get_cached(s.SCHEMA_CACHE_TTL_SECONDS, source_key)
    if raw is None:
        try:
            refresh_schema_cache()
        except Exception:
            logger.exception("report_template_consumer: refresh_schema_cache failed")
        raw = schema_cache.get_cached(s.SCHEMA_CACHE_TTL_SECONDS, source_key)
    if not raw:
        return []
    out: list[TableSchema] = []
    for item in raw:
        if isinstance(item, TableSchema):
            out.append(item)
        elif isinstance(item, dict):
            try:
                out.append(TableSchema.model_validate(item))
            except Exception:
                continue
    return out


async def _process_message(body: dict[str, Any]) -> None:
    source_key = str(body.get("analytics_source_key") or "").strip()
    if not source_key:
        logger.warning("report_template_consumer: missing analytics_source_key")
        return
    if count_distinct_system_schedule_types(source_key) >= 5:
        logger.info("report_template_consumer: skip %s (already complete)", source_key)
        return

    display = _display_name_for_source(source_key)
    tables = _tables_for_source(source_key)
    texts = await generate_five_template_texts(
        source_key=source_key, display_name=display, tables=tables
    )
    payload = build_bulk_templates_payload(source_key, texts, default_schedules_iso())

    s = get_settings()
    base = (s.REPORT_TASK_SERVICE_URL or "").strip().rstrip("/")
    token = (s.REPORT_TASK_INTERNAL_TOKEN or "").strip()
    if not base or not token:
        logger.error("report_template_consumer: REPORT_TASK_SERVICE_URL or token not set")
        return

    url = f"{base}/api/reports/internal/report-templates/bulk"
    headers = {"X-Report-Internal-Token": token, "Content-Type": "application/json"}
    async with httpx.AsyncClient(timeout=120.0) as client:
        r = await client.post(url, headers=headers, json=payload)
        if r.is_error:
            logger.error(
                "report_template_consumer: bulk failed %s %s",
                r.status_code,
                r.text[:500],
            )
            r.raise_for_status()
    logger.info("report_template_consumer: bulk OK for source_key=%s", source_key)


async def _consumer_main() -> None:
    s = get_settings()
    url = (
        f"amqp://{s.RABBITMQ_USER}:{s.RABBITMQ_PASSWORD}"
        f"@{s.RABBITMQ_HOST}:{s.RABBITMQ_PORT}/"
    )
    connection = await _connect_with_retries(url)
    try:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=2)
        queue = await channel.declare_queue(QUEUE_REPORT_TEMPLATE_PLAN_REQUEST, durable=True)

        async def on_message(message: aio_pika.IncomingMessage) -> None:
            async with message.process():
                try:
                    body = json.loads(message.body.decode("utf-8"))
                    await _process_message(body)
                except Exception:
                    logger.exception("report_template_consumer: handler failed")

        await queue.consume(on_message)
        await asyncio.Future()
    finally:
        await connection.close()


async def _runner() -> None:
    while True:
        try:
            await _consumer_main()
        except asyncio.CancelledError:
            break
        except Exception:
            logger.exception("report_template_consumer: crashed; reconnecting")
            await asyncio.sleep(5)


def start_report_template_consumer() -> None:
    global _task
    if _task is not None:
        return
    _task = asyncio.create_task(_runner())


async def stop_report_template_consumer() -> None:
    global _task
    if _task:
        _task.cancel()
        try:
            await _task
        except asyncio.CancelledError:
            pass
        _task = None


async def publish_template_plan_request(source_key: str) -> None:
    from app.services.rabbitmq_publish import rabbit_publish

    await rabbit_publish.publish_json(
        QUEUE_REPORT_TEMPLATE_PLAN_REQUEST,
        {"analytics_source_key": source_key.strip()},
    )
