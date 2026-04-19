from datetime import datetime, timedelta
from typing import Any, Dict

import jwt

from app.core.config import get_settings
from app.core.connection_manager import manager

settings = get_settings()


class WebSocketService:
    def get_websocket_url(self) -> str:
        """Путь WebSocket относительно BFF (через тот же nginx :80 или напрямую :8000)."""
        return "/api/websocket/ws"

    def get_connections_stats(self) -> Dict[str, Any]:
        return manager.stats()

    def create_websocket_token(self, user_id: str, email: str, role: str) -> Dict[str, Any]:
        expires_in = 3600
        token_data = {
            "uuid": user_id,
            "email": email,
            "role": role,
            "type": "websocket",
            "exp": datetime.utcnow() + timedelta(seconds=expires_in),
        }

        ws_token = jwt.encode(
            token_data,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM,
        )

        return {
            "ws_url": self.get_websocket_url(),
            "token": ws_token,
            "expires_in": expires_in,
            "message": "Подключайтесь к BFF: ws://<host>/api/websocket/ws?token=...",
        }
