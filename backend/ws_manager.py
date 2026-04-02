from fastapi import WebSocket
from typing import Dict, Set
import json
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, channel: str = "events"):
        await websocket.accept()
        if channel not in self.active_connections:
            self.active_connections[channel] = set()
        self.active_connections[channel].add(websocket)

    def disconnect(self, websocket: WebSocket, channel: str = "events"):
        if channel in self.active_connections:
            self.active_connections[channel].discard(websocket)

    async def broadcast(self, data: dict, channel: str = "events"):
        if channel not in self.active_connections:
            return
        dead = set()
        for ws in self.active_connections[channel]:
            try:
                await ws.send_json(data)
            except Exception:
                dead.add(ws)
        for ws in dead:
            self.active_connections[channel].discard(ws)


manager = ConnectionManager()
