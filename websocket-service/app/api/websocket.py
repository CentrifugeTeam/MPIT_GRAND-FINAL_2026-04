from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import jwt
from app.core.connection_manager import ConnectionManager
from app.core.config import get_settings

router = APIRouter()
manager = ConnectionManager()
settings = get_settings()

@router.get("/connections")
async def get_connections():
    """Получить количество активных соединений"""
    return {
        "active_connections": len(manager.active_connections),
        "rooms": list(manager.rooms.keys())
    }

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint с JWT аутентификацией"""
    await websocket.accept()

    try:
        # Получаем токен из query параметров
        token = websocket.query_params.get("token")
        if not token:
            await websocket.close(code=1008, reason="No token provided")
            return

        # Валидируем JWT токен
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

        # Добавляем соединение в менеджер
        await manager.connect(websocket, user_id, user_email)

        # Отправляем подтверждение подключения
        await websocket.send_json({
            "type": "connection_established",
            "user_id": user_id,
            "email": user_email,
            "message": "WebSocket connection established"
        })

        # Основной цикл обработки сообщений
        while True:
            try:
                # Получаем сообщение от клиента
                data = await websocket.receive_json()

                # Обрабатываем разные типы сообщений
                message_type = data.get("type")

                if message_type == "ping":
                    await websocket.send_json({"type": "pong"})

                elif message_type == "join_room":
                    room = data.get("room")
                    await manager.join_room(websocket, room)
                    await websocket.send_json({
                        "type": "room_joined",
                        "room": room,
                        "user_id": user_id
                    })

                elif message_type == "leave_room":
                    room = data.get("room")
                    await manager.leave_room(websocket, room)
                    await websocket.send_json({
                        "type": "room_left",
                        "room": room,
                        "user_id": user_id
                    })

                elif message_type == "send_message":
                    message = data.get("message")
                    room = data.get("room")
                    await manager.send_message_to_room(room, {
                        "type": "message",
                        "user_id": user_id,
                        "email": user_email,
                        "message": message,
                        "room": room,
                        "timestamp": data.get("timestamp")
                    })

                elif message_type == "typing":
                    room = data.get("room")
                    await manager.send_message_to_room(room, {
                        "type": "user_typing",
                        "user_id": user_id,
                        "email": user_email,
                        "room": room
                    })

                else:
                    # Эхо ответ для неизвестных типов сообщений
                    await websocket.send_json({
                        "type": "echo",
                        "original": data
                    })

            except WebSocketDisconnect:
                break
            except Exception as e:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Error processing message: {str(e)}"
                })

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except:
            pass
    finally:
        # Удаляем соединение из менеджера
        await manager.disconnect(websocket)
