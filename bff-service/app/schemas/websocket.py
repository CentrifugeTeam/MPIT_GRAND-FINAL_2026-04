from pydantic import BaseModel, ConfigDict
from typing import List, Optional

class WebSocketInfo(BaseModel):
    websocket_url: str
    message: str
    user_id: Optional[str] = None
    email: Optional[str] = None

class WebSocketToken(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "ws_url": "ws://localhost:8000/api/websocket/ws",
                "token": "eyJhbGciOi...",
                "expires_in": 3600,
                "message": "WebSocket token generated",
            }
        }
    )
    ws_url: str
    token: str
    expires_in: int
    message: str

class WebSocketConnections(BaseModel):
    active_connections: int
    rooms: List[str]
