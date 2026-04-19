import asyncio
import json
import logging
from typing import Optional

import aio_pika

from app.core.config import get_settings
from app.core.connection_manager import manager
from app.core.queues import QUEUE_GENERATE_RESULT

logger = logging.getLogger(__name__)

_task: Optional[asyncio.Task] = None


async def _consumer_main() -> None:
    settings = get_settings()
    url = (
        f"amqp://{settings.RABBITMQ_USER}:{settings.RABBITMQ_PASSWORD}"
        f"@{settings.RABBITMQ_HOST}:{settings.RABBITMQ_PORT}/"
    )
    connection = await aio_pika.connect_robust(url)
    try:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=10)
        queue = await channel.declare_queue(QUEUE_GENERATE_RESULT, durable=True)

        async def on_message(message: aio_pika.IncomingMessage) -> None:
            async with message.process():
                try:
                    body = json.loads(message.body.decode("utf-8"))
                    jid = body.get("job_id")
                    uid = body.get("user_id")
                    payload = {"type": "nl_sql_result", **body}
                    room = f"job:{jid}"
                    await manager.send_message_to_room(room, payload)
                    await manager.send_message_to_user(uid, payload)
                except Exception:
                    logger.exception("Failed to route nl_sql result")

        await queue.consume(on_message)
        # consume() только регистрирует callback и сразу возвращается — без ожидания
        # корутина завершалась, цикл в _runner открывал новое подключение в цикле.
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
            logger.exception("RabbitMQ consumer crashed; reconnecting")
            await asyncio.sleep(5)


def start_consumer() -> None:
    global _task
    if _task is not None:
        return
    _task = asyncio.create_task(_runner())


async def stop_consumer() -> None:
    global _task
    if _task:
        _task.cancel()
        try:
            await _task
        except asyncio.CancelledError:
            pass
        _task = None
