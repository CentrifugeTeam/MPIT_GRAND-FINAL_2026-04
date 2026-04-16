from fastapi import WebSocket
from typing import Dict, List, Set
import json
import asyncio

class ConnectionManager:
    def __init__(self):
        # Активные соединения: {websocket: {"user_id": str, "email": str}}
        self.active_connections: Dict[WebSocket, Dict] = {}
        # Комнаты: {room_name: Set[websocket]}
        self.rooms: Dict[str, Set[WebSocket]] = {}
        # Пользователи в комнатах: {room_name: {websocket: {"user_id": str, "email": str}}}
        self.room_users: Dict[str, Dict[WebSocket, Dict]] = {}

    async def connect(self, websocket: WebSocket, user_id: str, email: str):
        """Добавить новое соединение"""
        self.active_connections[websocket] = {
            "user_id": user_id,
            "email": email
        }

    async def disconnect(self, websocket: WebSocket):
        """Удалить соединение"""
        if websocket in self.active_connections:
            user_info = self.active_connections[websocket]
            user_id = user_info["user_id"]
            email = user_info["email"]

            # Удаляем из всех комнат
            for room_name in list(self.rooms.keys()):
                await self.leave_room(websocket, room_name)

            # Удаляем из активных соединений
            del self.active_connections[websocket]

    async def join_room(self, websocket: WebSocket, room: str):
        """Присоединить пользователя к комнате"""
        if websocket not in self.active_connections:
            return

        user_info = self.active_connections[websocket]

        # Создаем комнату если не существует
        if room not in self.rooms:
            self.rooms[room] = set()
            self.room_users[room] = {}

        # Добавляем в комнату
        self.rooms[room].add(websocket)
        self.room_users[room][websocket] = user_info

    async def leave_room(self, websocket: WebSocket, room: str):
        """Удалить пользователя из комнаты"""
        if room in self.rooms and websocket in self.rooms[room]:
            self.rooms[room].remove(websocket)
            if websocket in self.room_users[room]:
                del self.room_users[room][websocket]

            # Удаляем пустые комнаты
            if not self.rooms[room]:
                del self.rooms[room]
                del self.room_users[room]

    async def send_personal_message(self, websocket: WebSocket, message: dict):
        """Отправить личное сообщение"""
        try:
            await websocket.send_json(message)
        except:
            # Соединение закрыто, удаляем
            await self.disconnect(websocket)

    async def send_message_to_room(self, room: str, message: dict):
        """Отправить сообщение всем в комнате"""
        if room not in self.rooms:
            return

        # Создаем список задач для параллельной отправки
        tasks = []
        disconnected_websockets = []

        for websocket in self.rooms[room].copy():
            try:
                await websocket.send_json(message)
            except:
                # Соединение закрыто, помечаем для удаления
                disconnected_websockets.append(websocket)

        # Удаляем отключенные соединения
        for websocket in disconnected_websockets:
            await self.disconnect(websocket)

    async def send_message_to_user(self, user_id: str, message: dict):
        """Отправить сообщение конкретному пользователю"""
        for websocket, user_info in self.active_connections.items():
            if user_info["user_id"] == user_id:
                await self.send_personal_message(websocket, message)
                break

    def get_room_users(self, room: str) -> List[dict]:
        """Получить список пользователей в комнате"""
        if room not in self.room_users:
            return []

        return [
            {
                "user_id": user_info["user_id"],
                "email": user_info["email"]
            }
            for user_info in self.room_users[room].values()
        ]

    def get_user_rooms(self, user_id: str) -> List[str]:
        """Получить список комнат пользователя"""
        user_rooms = []
        for room, users in self.room_users.items():
            for websocket, user_info in users.items():
                if user_info["user_id"] == user_id:
                    user_rooms.append(room)
                    break
        return user_rooms
