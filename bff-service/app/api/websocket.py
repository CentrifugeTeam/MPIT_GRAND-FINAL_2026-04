from fastapi import APIRouter, HTTPException, Depends, status, WebSocket, WebSocketDisconnect
from app.services.websocket_service import WebSocketService
from app.schemas.websocket import WebSocketInfo, WebSocketConnections, WebSocketToken
from app.api.auth import get_current_user
import jwt
from app.core.config import get_settings

router = APIRouter()
websocket_service = WebSocketService()
settings = get_settings()

@router.post("/token", response_model=WebSocketToken)
async def get_websocket_token(current_user: dict = Depends(get_current_user)):
    """Получить токен для прямого подключения к WebSocket сервису"""
    try:
        token_data = websocket_service.create_websocket_token(
            user_id=current_user.get("uuid"),
            email=current_user.get("email"),
            role=current_user.get("role", "USER")
        )
        return WebSocketToken(**token_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create WebSocket token: {str(e)}"
        )

@router.get("/info", response_model=WebSocketInfo)
async def get_websocket_info(current_user: dict = Depends(get_current_user)):
    """Получить информацию о WebSocket сервисе (legacy)"""
    try:
        websocket_url = websocket_service.get_websocket_url()
        return WebSocketInfo(
            websocket_url=websocket_url,
            message="Connect to WebSocket Service with JWT token",
            user_id=current_user.get("uuid"),
            email=current_user.get("email")
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get WebSocket info: {str(e)}"
        )

@router.get("/connections", response_model=WebSocketConnections)
async def get_websocket_connections(current_user: dict = Depends(get_current_user)):
    """Получить информацию о WebSocket соединениях"""
    try:
        connections = await websocket_service.get_websocket_connections()
        return WebSocketConnections(**connections)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get connections: {str(e)}"
        )

@router.websocket("/ws")
async def websocket_proxy(websocket: WebSocket):
    """WebSocket прокси через BFF с JWT аутентификацией"""
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
                algorithms=[settings.ALGORITHM]
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


        await websocket.send_json({
            "type": "connection_established",
            "user_id": user_id,
            "email": user_email,
            "message": "WebSocket connection established via BFF",
            "proxy": "bff-service"
        })

        while True:
            try:
                data = await websocket.receive_json()

                message_type = data.get("type")

                if message_type == "ping":
                    await websocket.send_json({"type": "pong", "proxy": "bff-service"})
                elif message_type == "join_room":
                    room = data.get("room")
                    await websocket.send_json({
                        "type": "room_joined",
                        "room": room,
                        "user_id": user_id,
                        "proxy": "bff-service"
                    })
                elif message_type == "send_message":
                    message = data.get("message")
                    room = data.get("room")
                    await websocket.send_json({
                        "type": "message_sent",
                        "room": room,
                        "user_id": user_id,
                        "message": message,
                        "timestamp": data.get("timestamp"),
                        "proxy": "bff-service"
                    })
                else:
                    await websocket.send_json({
                        "type": "echo",
                        "original": data,
                        "proxy": "bff-service"
                    })

            except WebSocketDisconnect:
                break
            except Exception as e:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Error processing message: {str(e)}",
                    "proxy": "bff-service"
                })

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except:
            pass
