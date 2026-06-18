from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self.rooms : dict[int, set[WebSocket]] = {}


    async def connect(self, websocket: WebSocket, room_id: int):
        await websocket.accept()
        if not self.rooms[room_id]:
            self.rooms[room_id] = set()

    async def disconnect(self):
        pass
