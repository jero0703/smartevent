from fastapi import WebSocket
from typing import Dict, Set
import json
import asyncio
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        # event_id -> Set of WebSockets
        self.availability_connections: Dict[int, Set[WebSocket]] = {}
        self.updates_connections: Dict[int, Set[WebSocket]] = {}

    async def connect_availability(self, event_id: int, websocket: WebSocket):
        await websocket.accept()
        if event_id not in self.availability_connections:
            self.availability_connections[event_id] = set()
        self.availability_connections[event_id].add(websocket)

    def disconnect_availability(self, event_id: int, websocket: WebSocket):
        if event_id in self.availability_connections:
            self.availability_connections[event_id].discard(websocket)
            if not self.availability_connections[event_id]:
                del self.availability_connections[event_id]

    async def broadcast_availability(self, event_id: int, data: dict):
        if event_id not in self.availability_connections:
            return
        dead_connections = set()
        for ws in self.availability_connections[event_id]:
            try:
                await ws.send_json(data)
            except Exception as e:
                logger.warning(f"Failed to send to websocket: {e}")
                dead_connections.add(ws)
        for dead in dead_connections:
            self.disconnect_availability(event_id, dead)

    async def connect_updates(self, event_id: int, websocket: WebSocket):
        await websocket.accept()
        if event_id not in self.updates_connections:
            self.updates_connections[event_id] = set()
        self.updates_connections[event_id].add(websocket)

    def disconnect_updates(self, event_id: int, websocket: WebSocket):
        if event_id in self.updates_connections:
            self.updates_connections[event_id].discard(websocket)
            if not self.updates_connections[event_id]:
                del self.updates_connections[event_id]

    async def broadcast_event_update(self, event_id: int, data: dict):
        if event_id not in self.updates_connections:
            return
        dead_connections = set()
        for ws in self.updates_connections[event_id]:
            try:
                await ws.send_json(data)
            except Exception as e:
                logger.warning(f"Failed to send update to websocket: {e}")
                dead_connections.add(ws)
        for dead in dead_connections:
            self.disconnect_updates(event_id, dead)

manager = ConnectionManager()

def notify_availability_sync(event_id: int, total_capacity: int, tickets_sold: int, available_tickets: int):
    """
    Helper function to safely schedule an async broadcast from a synchronous service or thread.
    """
    payload = {
        "event_id": event_id,
        "total_capacity": total_capacity,
        "tickets_sold": tickets_sold,
        "available_tickets": available_tickets,
        "type": "availability_update"
    }
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(manager.broadcast_availability(event_id, payload))
    except RuntimeError:
        # No running event loop in current thread
        pass

def notify_event_update_sync(event_id: int, update_data: dict):
    """
    Helper function to safely schedule an announcement broadcast from a synchronous service.
    """
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(manager.broadcast_event_update(event_id, update_data))
    except RuntimeError:
        pass
