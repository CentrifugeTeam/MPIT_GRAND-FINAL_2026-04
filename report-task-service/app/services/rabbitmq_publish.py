from __future__ import annotations

import json

import aio_pika
from aio_pika import DeliveryMode, Message

from app.core.config import get_settings


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
