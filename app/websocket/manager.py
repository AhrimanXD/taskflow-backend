from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self.rooms: dict[int, set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room_id: int):
        if room_id not in self.rooms:
            self.rooms[room_id] = set()
        self.rooms[room_id].add(websocket)

    async def disconnect(self, websocket: WebSocket, room_id: int):
        if room_id in self.rooms:
            self.rooms[room_id].discard(websocket)
            if not self.rooms[room_id]:
                del self.rooms[room_id]

    async def broadcast(self, message: dict, room_id: int):
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


manager = ConnectionManager()
