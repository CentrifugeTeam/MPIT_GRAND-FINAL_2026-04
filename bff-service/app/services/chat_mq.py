import asyncio
import json
import logging
from typing import Any, Optional

import aio_pika
from aio_pika import DeliveryMode, Message

from app.core.config import get_settings
from app.core.connection_manager import manager
from app.core.queues import QUEUE_CHAT_INCOMING, QUEUE_CHAT_OUT

logger = logging.getLogger(__name__)

_CONNECT_RETRY_BASE_SEC = 1.0
_CONNECT_RETRY_MAX_SEC = 15.0


class ChatMqBus:
    """Публикация nl_chat_incoming и приём nl_chat_out → WebSocket комнаты chat:<conversation_id>."""

    def __init__(self) -> None:
        self._connection: Optional[aio_pika.RobustConnection] = None
        self._publish_channel: Optional[aio_pika.Channel] = None
        self._consume_channel: Optional[aio_pika.Channel] = None
        self._started = False

    async def _connect_with_retries(self, url: str) -> aio_pika.abc.AbstractRobustConnection:
        delay = _CONNECT_RETRY_BASE_SEC
        while True:
            try:
                return await aio_pika.connect_robust(url)
            except asyncio.CancelledError:
                raise
            except Exception as e:
                logger.warning(
                    "Chat RabbitMQ connect failed (%s). Retrying in %.1fs", e, delay
                )
                await asyncio.sleep(delay)
                delay = min(delay * 2, _CONNECT_RETRY_MAX_SEC)

    async def start(self) -> None:
        if self._started:
            return
        s = get_settings()
        url = (
            f"amqp://{s.RABBITMQ_USER}:{s.RABBITMQ_PASSWORD}"
            f"@{s.RABBITMQ_HOST}:{s.RABBITMQ_PORT}/"
        )
        self._connection = await self._connect_with_retries(url)
        self._publish_channel = await self._connection.channel()
        self._consume_channel = await self._connection.channel()
        await self._consume_channel.set_qos(prefetch_count=20)
        await self._publish_channel.declare_queue(QUEUE_CHAT_INCOMING, durable=True)
        q_out = await self._consume_channel.declare_queue(QUEUE_CHAT_OUT, durable=True)

        async def on_out(msg: aio_pika.IncomingMessage) -> None:
            async with msg.process():
                try:
                    body = json.loads(msg.body.decode("utf-8"))
                    cid = body.get("conversation_id")
                    if not cid:
                        return
                    room = f"chat:{cid}"
                    await manager.send_message_to_room(room, body)
                except Exception:
                    logger.exception("chat out routing failed")

        await q_out.consume(on_out)
        self._started = True
        logger.info("Chat MQ bus started (%s → WS)", QUEUE_CHAT_OUT)

    async def publish_incoming(self, payload: dict[str, Any]) -> None:
        if not self._publish_channel:
            raise RuntimeError("ChatMqBus not started")
        await self._publish_channel.default_exchange.publish(
            Message(
                body=json.dumps(payload, default=str).encode("utf-8"),
                delivery_mode=DeliveryMode.PERSISTENT,
            ),
            routing_key=QUEUE_CHAT_INCOMING,
        )

    async def stop(self) -> None:
        if self._publish_channel and not self._publish_channel.is_closed:
            await self._publish_channel.close()
        if self._consume_channel and not self._consume_channel.is_closed:
            await self._consume_channel.close()
        if self._connection and not self._connection.is_closed:
            await self._connection.close()
        self._publish_channel = None
        self._consume_channel = None
        self._connection = None
        self._started = False


chat_bus = ChatMqBus()
