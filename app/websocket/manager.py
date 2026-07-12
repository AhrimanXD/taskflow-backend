import uuid

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        # Workspace board rooms, keyed by workspace_id.
        self.rooms: dict[uuid.UUID, set[WebSocket]] = {}
        # Per-user notification channels, keyed by user_id — kept in a separate
        # dict so user ids never collide with workspace ids.
        self.user_rooms: dict[uuid.UUID, set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room_id: uuid.UUID):
        if room_id not in self.rooms:
            self.rooms[room_id] = set()
        self.rooms[room_id].add(websocket)

    async def disconnect(self, websocket: WebSocket, room_id: uuid.UUID):
        if room_id in self.rooms:
            self.rooms[room_id].discard(websocket)
            if not self.rooms[room_id]:
                del self.rooms[room_id]

    async def broadcast(self, message: dict, room_id: uuid.UUID):
        if room_id in self.rooms:
            room_copy = self.rooms[room_id].copy()
            dead_connections = set()
            for member in room_copy:
                try:
                    await member.send_json(message)
                except Exception:
                    dead_connections.add(member)
            for connections in dead_connections:
                await self.disconnect(connections, room_id)

    # --- Per-user notification channel -----------------------------------
    async def connect_user(self, websocket: WebSocket, user_id: uuid.UUID):
        if user_id not in self.user_rooms:
            self.user_rooms[user_id] = set()
        self.user_rooms[user_id].add(websocket)

    async def disconnect_user(self, websocket: WebSocket, user_id: uuid.UUID):
        if user_id in self.user_rooms:
            self.user_rooms[user_id].discard(websocket)
            if not self.user_rooms[user_id]:
                del self.user_rooms[user_id]

    async def send_to_user(self, message: dict, user_id: uuid.UUID):
        if user_id in self.user_rooms:
            room_copy = self.user_rooms[user_id].copy()
            dead = set()
            for ws in room_copy:
                try:
                    await ws.send_json(message)
                except Exception:
                    dead.add(ws)
            for ws in dead:
                await self.disconnect_user(ws, user_id)


manager = ConnectionManager()
