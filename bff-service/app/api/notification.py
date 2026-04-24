import asyncio
import json
import logging
import uuid

import httpx
import jwt
from fastapi import APIRouter, HTTPException, Depends, Query, Request, status
from fastapi.responses import StreamingResponse
from app.api.auth import get_current_user
from app.schemas.notification import (
    NotificationCreate,
    NotificationResponse,
    NotificationSettings,
    NotificationSettingsResponse,
    NotifyEnqueueResponse,
)
from app.services.notification_service import NotificationService
from app.services.notification_realtime import publish_notification_touch, stream_channel_name
from app.core.config import get_settings

router = APIRouter()
notification_service = NotificationService()
settings = get_settings()
logger = logging.getLogger(__name__)

# Redis: push через pub/sub, без constant GET. Без Redis: редкий poll.
FALLBACK_POLL_SECONDS = 45.0
PUBSUB_GET_MESSAGE_TIMEOUT = 30.0
# Раз в столько «тихих» циклов (только heartbeat) делаем сверку с БД — на случай записи мимо BFF.
REDIS_SAFETY_POLL_HEARTBEATS = 3
# Несколько publish подряд сливаем в один GET к notification-service.
REDIS_TOUCH_DEBOUNCE_SEC = 0.35
REDIS_DRAIN_MAX_MESSAGES = 256


def _rows_from_notification_raw(raw) -> list:
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict):
        return raw.get("notifications", [])
    return []


# Статичный путь ОБЯЗАН быть выше GET /{user_id}, иначе "stream" матчится как user_id и требуется HTTPBearer.
@router.get(
    "/stream",
    summary="SSE поток уведомлений",
    description="Поток новых уведомлений по токену (query). Обновления подтягиваются по Redis; без Redis — редкий poll.",
)
async def notification_stream(
    request: Request,
    token: str = Query(..., min_length=10),
):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = str(payload.get("uuid") or "")
        if not user_id:
            raise ValueError("invalid token payload")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    async def _event_gen():
        def _sig(rows: list) -> str:
            return json.dumps(rows, sort_keys=True, default=str)

        last_sig: str | None = None
        try:
            raw0 = await notification_service.get_user_notifications(user_id)
            rows0 = _rows_from_notification_raw(raw0)
            last_sig = _sig(rows0)
            yield f"event: notifications\ndata: {json.dumps({'notifications': rows0})}\n\n"
        except Exception as e:
            logger.warning("notification stream initial fetch failed: %s", e)
            yield "event: error\ndata: {\"message\":\"notification stream error\"}\n\n"
            return

        channel = stream_channel_name(user_id)
        rc = getattr(request.app.state, "redis_client", None)
        pubsub = None
        if rc:
            try:
                pubsub = rc.pubsub()
                await pubsub.subscribe(channel)
            except Exception as e:
                logger.warning("notification stream pubsub subscribe failed: %s", e)
                pubsub = None

        if pubsub:
            idle_heartbeats = 0
            try:
                while True:
                    if await request.is_disconnected():
                        break
                    try:
                        msg = await pubsub.get_message(
                            ignore_subscribe_messages=True,
                            timeout=PUBSUB_GET_MESSAGE_TIMEOUT,
                        )
                    except Exception as e:
                        logger.warning("notification stream get_message: %s", e)
                        msg = None
                    if await request.is_disconnected():
                        break
                    if msg and msg.get("type") == "message":
                        idle_heartbeats = 0
                        # Один сигнал Redis = много publish подряд → без debounce спамим GET.
                        await asyncio.sleep(REDIS_TOUCH_DEBOUNCE_SEC)
                        if await request.is_disconnected():
                            break
                        drained = 0
                        while drained < REDIS_DRAIN_MAX_MESSAGES:
                            extra = await pubsub.get_message(
                                ignore_subscribe_messages=True,
                                timeout=0.001,
                            )
                            if not extra or extra.get("type") != "message":
                                break
                            drained += 1
                        try:
                            raw = await notification_service.get_user_notifications(user_id)
                            rows = _rows_from_notification_raw(raw)
                            sig = _sig(rows)
                            if sig != last_sig:
                                last_sig = sig
                                yield f"event: notifications\ndata: {json.dumps({'notifications': rows})}\n\n"
                        except Exception as e:
                            logger.warning("notification stream fetch after push failed: %s", e)
                            yield "event: error\ndata: {\"message\":\"notification stream error\"}\n\n"
                    else:
                        idle_heartbeats += 1
                        if idle_heartbeats >= REDIS_SAFETY_POLL_HEARTBEATS:
                            idle_heartbeats = 0
                            try:
                                raw = await notification_service.get_user_notifications(user_id)
                                rows = _rows_from_notification_raw(raw)
                                sig = _sig(rows)
                                if sig != last_sig:
                                    last_sig = sig
                                    yield f"event: notifications\ndata: {json.dumps({'notifications': rows})}\n\n"
                            except Exception as e:
                                logger.warning("notification stream safety poll failed: %s", e)
                        yield "event: heartbeat\ndata: {}\n\n"
            finally:
                try:
                    await pubsub.unsubscribe(channel)
                except Exception:
                    pass
                try:
                    await pubsub.aclose()
                except Exception:
                    try:
                        await pubsub.close()  # type: ignore[func-returns-value]
                    except Exception:
                        pass
        else:
            while True:
                if await request.is_disconnected():
                    break
                await asyncio.sleep(FALLBACK_POLL_SECONDS)
                if await request.is_disconnected():
                    break
                try:
                    raw = await notification_service.get_user_notifications(user_id)
                    rows = _rows_from_notification_raw(raw)
                    sig = _sig(rows)
                    if sig != last_sig:
                        last_sig = sig
                        yield f"event: notifications\ndata: {json.dumps({'notifications': rows})}\n\n"
                    else:
                        yield "event: heartbeat\ndata: {}\n\n"
                except Exception as e:
                    logger.warning("notification stream fallback poll failed: %s", e)
                    yield "event: error\ndata: {\"message\":\"notification stream error\"}\n\n"

    return StreamingResponse(
        _event_gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@router.delete(
    "/{user_id}/notification/{notification_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить уведомление",
    responses={403: {"description": "Чужой user_id"}, 404: {"description": "Не найдено"}},
)
async def delete_notification(
    user_id: str,
    notification_id: uuid.UUID,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    if current_user.get("uuid") != user_id and current_user.get("role") != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    try:
        await notification_service.delete_notification(user_id, str(notification_id))
    except httpx.HTTPStatusError as e:
        if e.response is not None and e.response.status_code == 404:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found") from e
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    await publish_notification_touch(getattr(request.app.state, "redis_client", None), user_id)


@router.post(
    "/{user_id}",
    response_model=NotificationResponse,
    summary="Создать уведомление",
    description="Свой user_id или ADMIN. Email подмешивается из JWT.",
    responses={403: {"description": "Чужой user_id"}, 400: {"description": "Ошибка notification-service"}},
)
async def create_notification(
    user_id: str,
    request: Request,
    notification_data: NotificationCreate,
    current_user: dict = Depends(get_current_user),
):
    try:
        if current_user.get("uuid") != user_id and current_user.get("role") != "ADMIN":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
            )

        notification_data_with_email = notification_data.model_dump()
        notification_data_with_email["email"] = current_user.get("email")

        notification = await notification_service.create_notification(
            user_id,
            notification_data_with_email,
        )
        await publish_notification_touch(getattr(request.app.state, "redis_client", None), user_id)
        return notification
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/{user_id}/notify",
    response_model=NotifyEnqueueResponse,
    summary="Поставить уведомление в очередь RabbitMQ",
    description="Асинхронная доставка через notification-worker.",
    responses={403: {"description": "Чужой user_id"}},
)
async def send_notification(
    user_id: str,
    request: Request,
    notification_data: NotificationCreate,
    current_user: dict = Depends(get_current_user),
):
    try:
        if current_user.get("uuid") != user_id and current_user.get("role") != "ADMIN":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
            )

        notification_data_with_email = notification_data.model_dump()
        notification_data_with_email["email"] = current_user.get("email")

        result = await notification_service.send_notification_to_queue(
            user_id,
            notification_data_with_email,
        )
        await publish_notification_touch(getattr(request.app.state, "redis_client", None), user_id)
        if isinstance(result, dict):
            nid = str(result.get("notification_id") or "")
        else:
            nid = str(result or "")
        return NotifyEnqueueResponse(
            message="Notification sent to queue",
            notification_id=nid,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/{user_id}/settings",
    response_model=NotificationSettingsResponse,
    summary="Настройки уведомлений",
    description="Свой user_id или ADMIN.",
    responses={403: {"description": "Чужой user_id"}},
)
async def get_notification_settings(
    user_id: str,
    current_user: dict = Depends(get_current_user),
):
    try:
        if current_user.get("uuid") != user_id and current_user.get("role") != "ADMIN":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
            )

        settings_out = await notification_service.get_notification_settings(user_id)
        return settings_out
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get notification settings: {str(e)}",
        )


@router.post(
    "/{user_id}/settings",
    response_model=NotificationSettingsResponse,
    summary="Обновить настройки уведомлений",
    description="Свой user_id или ADMIN.",
    responses={403: {"description": "Чужой user_id"}},
)
async def update_notification_settings(
    user_id: str,
    settings_data: NotificationSettings,
    current_user: dict = Depends(get_current_user),
):
    try:
        if current_user.get("uuid") != user_id and current_user.get("role") != "ADMIN":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
            )

        updated_settings = await notification_service.update_notification_settings(
            user_id,
            settings_data.model_dump(),
        )
        return updated_settings
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
