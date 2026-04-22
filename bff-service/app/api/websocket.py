import logging
import uuid

import jwt
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status

from app.schemas.websocket import WebSocketInfo, WebSocketConnections, WebSocketToken
from app.api.auth import get_current_user
from app.services.websocket_service import WebSocketService
from app.core.config import get_settings
from app.core.connection_manager import manager
from app.services.analytics_schema_client import fetch_public_schema
from app.services.chat_mq import chat_bus

router = APIRouter()
websocket_service = WebSocketService()
settings = get_settings()
logger = logging.getLogger(__name__)


def _nl_chat_blocked_source_keys() -> frozenset[str]:
    raw = (settings.NL_CHAT_BLOCKED_SOURCE_KEYS or "").strip()
    if not raw:
        return frozenset()
    return frozenset(x.strip().lower() for x in raw.split(",") if x.strip())


async def _safe_send_json(websocket: WebSocket, data: dict) -> None:
    """Клиент мог уже закрыть сокет (например сразу после leave_job) — не падаем в обработчике ошибок."""
    try:
        await websocket.send_json(data)
    except Exception:
        pass


@router.post("/token", response_model=WebSocketToken)
async def get_websocket_token(current_user: dict = Depends(get_current_user)):
    try:
        token_data = websocket_service.create_websocket_token(
            user_id=current_user.get("uuid"),
            email=current_user.get("email"),
            role=current_user.get("role", "USER"),
        )
        return WebSocketToken(**token_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create WebSocket token: {str(e)}",
        )


@router.get("/info", response_model=WebSocketInfo)
async def get_websocket_info(current_user: dict = Depends(get_current_user)):
    return WebSocketInfo(
        websocket_url=websocket_service.get_websocket_url(),
        message="WebSocket BFF: watch_job → job:<uuid>; join_chat → chat:<uuid> для NL-чата",
        user_id=current_user.get("uuid"),
        email=current_user.get("email"),
    )


@router.get("/connections", response_model=WebSocketConnections)
async def get_websocket_connections(current_user: dict = Depends(get_current_user)):
    stats = websocket_service.get_connections_stats()
    room_names = list(manager.rooms.keys())
    return WebSocketConnections(
        active_connections=stats.get("active_connections", 0),
        rooms=room_names,
    )


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    try:
        token = websocket.query_params.get("token")
        if not token:
            await websocket.close(code=1008, reason="No token provided")
            return

        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM],
            )
            user_id = payload.get("uuid")
            user_email = payload.get("email")
            user_role = str(payload.get("role") or "USER")

            if not user_id:
                await websocket.close(code=1008, reason="Invalid token payload")
                return

        except jwt.ExpiredSignatureError:
            await websocket.close(code=1008, reason="Token has expired")
            return
        except jwt.JWTError:
            await websocket.close(code=1008, reason="Invalid token")
            return

        await manager.connect(websocket, user_id, user_email or "")
        await _safe_send_json(
            websocket,
            {
                "type": "connection_established",
                "user_id": user_id,
                "email": user_email,
                "message": "WebSocket BFF",
            },
        )

        while True:
            try:
                data = await websocket.receive_json()
                message_type = data.get("type")

                if message_type == "ping":
                    await _safe_send_json(websocket, {"type": "pong"})
                elif message_type == "watch_job":
                    jid = data.get("job_id")
                    if jid:
                        room = f"job:{jid}"
                        await manager.join_room(websocket, room)
                        await _safe_send_json(
                            websocket,
                            {
                                "type": "watch_job_ack",
                                "job_id": jid,
                                "room": room,
                            },
                        )
                    else:
                        await _safe_send_json(
                            websocket,
                            {"type": "error", "message": "job_id required"},
                        )
                elif message_type == "leave_job":
                    jid = data.get("job_id")
                    if jid:
                        await manager.leave_room(websocket, f"job:{jid}")
                        await _safe_send_json(
                            websocket,
                            {"type": "left_job", "job_id": jid},
                        )
                elif message_type == "join_room":
                    room = data.get("room")
                    if room:
                        await manager.join_room(websocket, room)
                        await _safe_send_json(
                            websocket,
                            {"type": "room_joined", "room": room},
                        )
                elif message_type == "join_chat":
                    cid = data.get("conversation_id")
                    if cid:
                        room = f"chat:{cid}"
                        await manager.join_room(websocket, room)
                        await _safe_send_json(
                            websocket,
                            {
                                "type": "join_chat_ack",
                                "conversation_id": cid,
                                "room": room,
                            },
                        )
                    else:
                        await _safe_send_json(
                            websocket,
                            {"type": "error", "message": "conversation_id required"},
                        )
                elif message_type == "leave_chat":
                    cid = data.get("conversation_id")
                    if cid:
                        await manager.leave_room(websocket, f"chat:{cid}")
                        await _safe_send_json(
                            websocket,
                            {"type": "left_chat", "conversation_id": cid},
                        )
                elif message_type == "chat_message":
                    conv = data.get("conversation_id")
                    content = data.get("content")
                    history = data.get("history") or []
                    if not conv or not content:
                        await _safe_send_json(
                            websocket,
                            {
                                "type": "error",
                                "message": "conversation_id and content required",
                            },
                        )
                    else:
                        ask = data.get("analytics_source_key")
                        sk = (
                            str(ask).strip()
                            if isinstance(ask, str) and str(ask).strip()
                            else None
                        )
                        explicit_source_key = sk is not None
                        if not sk:
                            dk = (settings.DEFAULT_ANALYTICS_SOURCE_KEY or "").strip()
                            if dk:
                                sk = dk
                        blocked = _nl_chat_blocked_source_keys()
                        # Blocklist avoids accidental NL against platform DB when no key is sent.
                        # If the client explicitly sends analytics_source_key (UI source), honor it.
                        if (
                            sk
                            and blocked
                            and sk.lower() in blocked
                            and not explicit_source_key
                        ):
                            dk = (settings.DEFAULT_ANALYTICS_SOURCE_KEY or "").strip()
                            if dk and dk.lower() != sk.lower():
                                logger.info(
                                    "chat_message analytics_source_key %r coerced to %r (blocked for NL)",
                                    sk,
                                    dk,
                                )
                                sk = dk
                        try:
                            schema_tables = await fetch_public_schema(
                                sk, user_id=str(user_id), user_role=user_role
                            )
                        except Exception as e:
                            await _safe_send_json(
                                websocket,
                                {
                                    "type": "error",
                                    "message": f"schema: {e}",
                                },
                            )
                        else:
                            mid = data.get("message_id") or str(uuid.uuid4())
                            max_rows = data.get("max_rows")
                            max_rows_out: int | None = None
                            if isinstance(max_rows, int) and max_rows > 0:
                                max_rows_out = min(50_000_000, max_rows)
                            gc = data.get("glossary_context")
                            glossary_context = (
                                str(gc) if isinstance(gc, str) and gc.strip() else None
                            )
                            incoming: dict = {
                                "message_id": mid,
                                "user_id": user_id,
                                "user_role": user_role,
                                "conversation_id": str(conv),
                                "content": str(content),
                                "history": history
                                if isinstance(history, list)
                                else [],
                                "schema_tables": schema_tables,
                            }
                            if max_rows_out is not None:
                                incoming["max_rows"] = max_rows_out
                            if glossary_context is not None:
                                incoming["glossary_context"] = glossary_context
                            if sk is not None:
                                incoming["analytics_source_key"] = sk
                            raw_lbl = data.get("analytics_source_label")
                            if isinstance(raw_lbl, str) and raw_lbl.strip():
                                incoming["analytics_source_label"] = raw_lbl.strip()
                            await chat_bus.publish_incoming(incoming)
                            await _safe_send_json(
                                websocket,
                                {
                                    "type": "chat_message_ack",
                                    "message_id": mid,
                                    "conversation_id": str(conv),
                                },
                            )
                else:
                    await _safe_send_json(
                        websocket,
                        {"type": "echo", "original": data},
                    )

            except WebSocketDisconnect:
                break
            except Exception as e:
                await _safe_send_json(
                    websocket,
                    {"type": "error", "message": str(e)},
                )

    finally:
        await manager.disconnect(websocket)
