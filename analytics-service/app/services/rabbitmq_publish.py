import asyncio
import json
import logging
from typing import Any

import aio_pika

from app.core.config import get_settings
from app.core.queues import QUEUE_GENERATE_REQUEST

logger = logging.getLogger(__name__)


class RabbitPublish:
    _connection: aio_pika.RobustConnection | None = None
    _retry_base_sec: float = 1.0
    _retry_max_sec: float = 15.0

    async def _connect_with_retries(self, url: str) -> aio_pika.RobustConnection:
        delay = self._retry_base_sec
        while True:
            try:
                return await aio_pika.connect_robust(url)
            except asyncio.CancelledError:
                raise
            except Exception as e:
                logger.warning(
                    "RabbitMQ connect failed (%s). Retrying in %.1fs", e, delay
                )
                await asyncio.sleep(delay)
                delay = min(delay * 2, self._retry_max_sec)

    async def connect(self) -> None:
        if self._connection and not self._connection.is_closed:
            return
        s = get_settings()
        url = (
            f"amqp://{s.RABBITMQ_USER}:{s.RABBITMQ_PASSWORD}"
            f"@{s.RABBITMQ_HOST}:{s.RABBITMQ_PORT}/"
        )
        self._connection = await self._connect_with_retries(url)

    async def close(self) -> None:
        if self._connection and not self._connection.is_closed:
            await self._connection.close()

    async def publish_generate_request(self, payload: dict[str, Any]) -> None:
        await self.connect()
        assert self._connection is not None
        ch = await self._connection.channel()
        await ch.declare_queue(QUEUE_GENERATE_REQUEST, durable=True)
        body = json.dumps(payload, default=str).encode("utf-8")
        await ch.default_exchange.publish(
            aio_pika.Message(body=body, delivery_mode=aio_pika.DeliveryMode.PERSISTENT),
            routing_key=QUEUE_GENERATE_REQUEST,
        )
        await ch.close()


rabbit_publish = RabbitPublish()
