import httpx
import jwt
from datetime import datetime, timedelta
from typing import Dict, Any
from fastapi import HTTPException, status
from app.core.config import get_settings

settings = get_settings()

class WebSocketService:
    def __init__(self):
        self.websocket_service_url = "http://websocket-service:8008"

    async def get_websocket_connections(self) -> Dict[str, Any]:
        """Получить информацию о WebSocket соединениях"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.websocket_service_url}/connections")
                response.raise_for_status()
                return response.json()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get WebSocket connections: {str(e)}"
            )

    def get_websocket_url(self) -> str:
        """Получить URL для WebSocket соединения через BFF (legacy)"""
        return f"ws://bff-service:8000/api/websocket/ws"

    def create_websocket_token(self, user_id: str, email: str, role: str) -> Dict[str, Any]:
        """Создать токен для прямого подключения к WebSocket-service"""
        expires_in = 300
        token_data = {
            "uuid": user_id,
            "email": email,
            "role": role,
            "type": "websocket",
            "exp": datetime.utcnow() + timedelta(seconds=expires_in)
        }

        ws_token = jwt.encode(
            token_data,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )

        ws_path = "/ws-direct/ws"

        return {
            "ws_url": ws_path,
            "token": ws_token,
            "expires_in": expires_in,
            "message": "Connect to WebSocket service directly with this token"
        }
