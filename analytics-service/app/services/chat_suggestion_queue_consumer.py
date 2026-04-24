from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Optional

import aio_pika
from sqlalchemy import text

from app.core.config import get_settings
from app.core.queues import QUEUE_CHAT_SUGGESTION_PLAN_REQUEST
from app.db.platform_session import platform_engine
from app.schemas.analytics import TableSchema
from app.services import schema_cache
from app.services.chat_suggestion_plan_llm import generate_chat_suggestion_topics
from app.services.chat_suggestions_store import (
    get_system_suggestions_stats,
    list_source_keys_without_system_chat_suggestions,
    upsert_system_chat_suggestions,
)
from app.services.data_sources_store import list_active_source_keys
from app.services.rabbitmq_publish import rabbit_publish
from app.services.schema_scheduler import refresh_schema_cache

logger = logging.getLogger(__name__)

_task: Optional[asyncio.Task] = None
_CONNECT_RETRY_BASE_SEC = 1.0
_CONNECT_RETRY_MAX_SEC = 15.0
_DEFAULT_LOCALE = "ru"


async def _connect_with_retries(url: str) -> aio_pika.abc.AbstractRobustConnection:
    delay = _CONNECT_RETRY_BASE_SEC
    while True:
        try:
            return await aio_pika.connect_robust(url)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.warning("FAQ RabbitMQ connect failed (%s). Retrying in %.1fs", e, delay)
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
        logger.exception("faq_consumer: display_name lookup failed")
    return source_key


def _tables_for_source(source_key: str) -> list[TableSchema]:
    s = get_settings()
    raw = schema_cache.get_cached(s.SCHEMA_CACHE_TTL_SECONDS, source_key)
    if raw is None:
        try:
            refresh_schema_cache()
        except Exception:
            logger.exception("faq_consumer: refresh_schema_cache failed")
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
    source_key = str(body.get("analytics_source_key") or "").strip().lower()
    if not source_key:
        logger.warning("faq_consumer: missing analytics_source_key")
        return
    stats = get_system_suggestions_stats(source_key, locale=_DEFAULT_LOCALE)
    if stats["questions"] >= 4:
        logger.info("faq_consumer: skip %s (already has FAQ)", source_key)
        return
    display = _display_name_for_source(source_key)
    tables = _tables_for_source(source_key)
    topics = await generate_chat_suggestion_topics(
        source_key=source_key,
        display_name=display,
        tables=tables,
        locale=_DEFAULT_LOCALE,
    )
    inserted = upsert_system_chat_suggestions(
        source_key=source_key,
        topics=topics,
        locale=_DEFAULT_LOCALE,
    )
    logger.info("faq_consumer: upserted %s rows for source_key=%s", inserted, source_key)


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
        queue = await channel.declare_queue(QUEUE_CHAT_SUGGESTION_PLAN_REQUEST, durable=True)

        async def on_message(message: aio_pika.IncomingMessage) -> None:
            async with message.process():
                try:
                    body = json.loads(message.body.decode("utf-8"))
                    await _process_message(body)
                except Exception:
                    logger.exception("faq_consumer: handler failed")

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
            logger.exception("faq_consumer: crashed; reconnecting")
            await asyncio.sleep(5)


def start_chat_suggestion_consumer() -> None:
    global _task
    if _task is not None:
        return
    _task = asyncio.create_task(_runner())


async def stop_chat_suggestion_consumer() -> None:
    global _task
    if _task:
        _task.cancel()
        try:
            await _task
        except asyncio.CancelledError:
            pass
        _task = None


async def publish_chat_suggestion_plan_request(source_key: str) -> None:
    sk = (source_key or "").strip().lower()
    if not sk:
        return
    await rabbit_publish.publish_json(
        QUEUE_CHAT_SUGGESTION_PLAN_REQUEST,
        {"analytics_source_key": sk},
    )


async def enqueue_missing_chat_suggestion_sources() -> int:
    # Prefer strict stats check against all active keys.
    count = 0
    keys = list_active_source_keys()
    if not keys:
        keys = list_source_keys_without_system_chat_suggestions(locale=_DEFAULT_LOCALE)
    for sk in keys:
        stats = get_system_suggestions_stats(sk, locale=_DEFAULT_LOCALE)
        if stats["questions"] >= 4:
            continue
        await publish_chat_suggestion_plan_request(sk)
        count += 1
    return count
