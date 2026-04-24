"""Redis pub/sub: push-события для SSE без constant polling к notification-service."""

from __future__ import annotations

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Канал на пользователя: подписчики SSE ждут сообщений, не снимок данных.
def stream_channel_name(user_id: str) -> str:
    return f"notif:stream:{user_id}"


async def publish_notification_touch(redis_client: Optional[Any], user_id: str) -> None:
    """Сигнал подписчикам: список уведомлений у user_id обновился (любой payload)."""
    if not redis_client or not (user_id or "").strip():
        return
    try:
        await redis_client.publish(stream_channel_name(user_id), "1")
    except Exception as e:
        logger.warning("notification publish failed for %s: %s", user_id, e)
