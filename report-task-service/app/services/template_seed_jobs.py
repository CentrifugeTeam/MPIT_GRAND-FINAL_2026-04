"""Постановка в очередь задач на автогенерацию системных шаблонов по источникам данных."""

from __future__ import annotations

import asyncio
import logging

from sqlalchemy import text

from app.core.queues import QUEUE_REPORT_TEMPLATE_PLAN_REQUEST
from app.db.session import platform_engine
from app.services import template_store
from app.services.rabbitmq_publish import rabbit_publish

logger = logging.getLogger(__name__)


def _list_analytics_source_keys() -> list[str]:
    eng = platform_engine()
    with eng.connect() as conn:
        rows = conn.execute(
            text("SELECT source_key FROM analytics_data_sources ORDER BY source_key")
        ).fetchall()
    return [str(r[0]) for r in rows if r and r[0]]


async def enqueue_missing_template_plans() -> None:
    """Для каждого источника, у которого нет 5 системных шаблонов, публикуем сообщение в RabbitMQ."""
    try:
        await rabbit_publish.wait_until_connected()
    except Exception:
        logger.exception(
            "template_seed: RabbitMQ недоступен после ретраев, пропускаем постановку в очередь"
        )
        return

    try:
        keys = _list_analytics_source_keys()
    except Exception:
        logger.exception("template_seed: failed to list analytics_data_sources")
        return

    for key in keys:
        try:
            n = template_store.system_template_schedule_types_count(key)
        except Exception:
            logger.exception("template_seed: count failed for source_key=%s", key)
            continue
        if n >= len(template_store.SCHEDULE_TYPES):
            continue
        try:
            await rabbit_publish.publish_json(
                QUEUE_REPORT_TEMPLATE_PLAN_REQUEST,
                {"analytics_source_key": key},
            )
            logger.info(
                "template_seed: enqueued plan for source_key=%s (had %s/%s schedule types)",
                key,
                n,
                len(template_store.SCHEDULE_TYPES),
            )
        except Exception:
            logger.exception("template_seed: publish failed for source_key=%s", key)


def start_background_template_seed() -> None:
    """Не блокирует bind порта: короткая пауза, затем ожидание Rabbit и постановка в очередь."""

    async def _runner() -> None:
        await asyncio.sleep(1.0)
        await enqueue_missing_template_plans()

    asyncio.create_task(_runner())
