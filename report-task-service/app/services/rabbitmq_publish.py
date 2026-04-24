from __future__ import annotations

import asyncio
import json
import logging

import aio_pika
from aio_pika import DeliveryMode, Message

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class RabbitPublishService:
    def __init__(self) -> None:
        self._conn: aio_pika.RobustConnection | None = None
        self._channel: aio_pika.Channel | None = None

    async def _ensure(self) -> aio_pika.Channel:
        if self._channel and not self._channel.is_closed:
            return self._channel
        s = get_settings()
        url = (
            f"amqp://{s.RABBITMQ_USER}:{s.RABBITMQ_PASSWORD}"
            f"@{s.RABBITMQ_HOST}:{s.RABBITMQ_PORT}/"
        )
        self._conn = await aio_pika.connect_robust(url)
        self._channel = await self._conn.channel()
        return self._channel

    async def wait_until_connected(
        self,
        *,
        deadline_sec: float = 120.0,
        initial_delay_sec: float = 0.5,
        max_delay_sec: float = 6.0,
    ) -> None:
        """Ждёт, пока RabbitMQ примет TCP (старт compose часто позже report-task-service)."""
        loop = asyncio.get_running_loop()
        deadline = loop.time() + deadline_sec
        delay = initial_delay_sec
        last_err: BaseException | None = None
        attempt = 0
        while loop.time() < deadline:
            try:
                await self._ensure()
                return
            except (asyncio.CancelledError, KeyboardInterrupt):
                raise
            except BaseException as e:
                last_err = e
                attempt += 1
                logger.warning(
                    "RabbitMQ not ready (%s). attempt %s, retry in %.1fs",
                    e,
                    attempt,
                    delay,
                )
                await asyncio.sleep(delay)
                delay = min(delay * 1.5, max_delay_sec)
                self._channel = None
                if self._conn is not None:
                    try:
                        await self._conn.close()
                    except Exception:
                        pass
                self._conn = None
        assert last_err is not None
        raise last_err

    async def publish_json(self, queue_name: str, payload: dict) -> None:
        ch = await self._ensure()
        await ch.declare_queue(queue_name, durable=True)
        await ch.default_exchange.publish(
            Message(
                body=json.dumps(payload, default=str).encode("utf-8"),
                delivery_mode=DeliveryMode.PERSISTENT,
            ),
            routing_key=queue_name,
        )


rabbit_publish = RabbitPublishService()
