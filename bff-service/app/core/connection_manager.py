from typing import Dict, Set

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: Dict[WebSocket, Dict] = {}
        self.rooms: Dict[str, Set[WebSocket]] = {}
        self.room_users: Dict[str, Dict[WebSocket, Dict]] = {}

    async def connect(self, websocket: WebSocket, user_id: str, email: str) -> None:
        self.active_connections[websocket] = {"user_id": user_id, "email": email}

    async def disconnect(self, websocket: WebSocket) -> None:
        if websocket not in self.active_connections:
            return
        for room_name in list(self.rooms.keys()):
            await self.leave_room(websocket, room_name)
        del self.active_connections[websocket]

    async def join_room(self, websocket: WebSocket, room: str) -> None:
        if websocket not in self.active_connections:
            return
        user_info = self.active_connections[websocket]
        if room not in self.rooms:
            self.rooms[room] = set()
            self.room_users[room] = {}
        self.rooms[room].add(websocket)
        self.room_users[room][websocket] = user_info

    async def leave_room(self, websocket: WebSocket, room: str) -> None:
        if room in self.rooms and websocket in self.rooms[room]:
            self.rooms[room].remove(websocket)
            if websocket in self.room_users.get(room, {}):
                del self.room_users[room][websocket]
            if not self.rooms[room]:
                del self.rooms[room]
                del self.room_users[room]

    async def send_personal_message(self, websocket: WebSocket, message: dict) -> None:
        try:
            await websocket.send_json(message)
        except Exception:
            await self.disconnect(websocket)

    async def send_message_to_room(self, room: str, message: dict) -> None:
        if room not in self.rooms:
            return
        for websocket in list(self.rooms[room]):
            await self.send_personal_message(websocket, message)

    async def send_message_to_user(self, user_id: str, message: dict) -> None:
        for websocket, user_info in list(self.active_connections.items()):
            if user_info["user_id"] == user_id:
                await self.send_personal_message(websocket, message)

    def stats(self) -> dict:
        return {
            "active_connections": len(self.active_connections),
            "rooms": len(self.rooms),
        }


manager = ConnectionManager()
