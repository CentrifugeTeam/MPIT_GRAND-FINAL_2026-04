from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
import jwt

from app.schemas.websocket import WebSocketInfo, WebSocketConnections, WebSocketToken
from app.api.auth import get_current_user
from app.services.websocket_service import WebSocketService
from app.core.config import get_settings
from app.core.connection_manager import manager

router = APIRouter()
websocket_service = WebSocketService()
settings = get_settings()


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
        message="WebSocket на BFF: после подключения отправьте watch_job для комнаты job:<uuid>",
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
        await websocket.send_json(
            {
                "type": "connection_established",
                "user_id": user_id,
                "email": user_email,
                "message": "WebSocket BFF",
            }
        )

        while True:
            try:
                data = await websocket.receive_json()
                message_type = data.get("type")

                if message_type == "ping":
                    await websocket.send_json({"type": "pong"})
                elif message_type == "watch_job":
                    jid = data.get("job_id")
                    if jid:
                        room = f"job:{jid}"
                        await manager.join_room(websocket, room)
                        await websocket.send_json(
                            {
                                "type": "watch_job_ack",
                                "job_id": jid,
                                "room": room,
                            }
                        )
                    else:
                        await websocket.send_json(
                            {"type": "error", "message": "job_id required"}
                        )
                elif message_type == "leave_job":
                    jid = data.get("job_id")
                    if jid:
                        await manager.leave_room(websocket, f"job:{jid}")
                        await websocket.send_json(
                            {"type": "left_job", "job_id": jid}
                        )
                elif message_type == "join_room":
                    room = data.get("room")
                    if room:
                        await manager.join_room(websocket, room)
                        await websocket.send_json(
                            {"type": "room_joined", "room": room}
                        )
                else:
                    await websocket.send_json({"type": "echo", "original": data})

            except WebSocketDisconnect:
                break
            except Exception as e:
                await websocket.send_json({"type": "error", "message": str(e)})

    finally:
        await manager.disconnect(websocket)
