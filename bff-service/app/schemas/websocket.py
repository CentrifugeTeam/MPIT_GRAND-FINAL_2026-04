from pydantic import BaseModel
from typing import List, Optional

class WebSocketInfo(BaseModel):
    websocket_url: str
    message: str
    user_id: Optional[str] = None
    email: Optional[str] = None

class WebSocketToken(BaseModel):
    ws_url: str
    token: str
    expires_in: int
    message: str

class WebSocketConnections(BaseModel):
    active_connections: int
    rooms: List[str]
