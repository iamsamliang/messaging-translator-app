from fastapi import WebSocket


class ConnectionManager:
    """Class defining socket events"""

    def __init__(self) -> None:
        # {chat_id: [websockets in this chat]}
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str, sender: WebSocket, chat_id: int) -> None:
        for connection in self.active_connections:
            if connection is not sender:
                await connection.send_text(message)
