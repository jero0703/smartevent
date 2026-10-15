from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from app.utils.websocket_manager import manager
from app.core.database import get_db
from app.services.availability_service import get_event_availability
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["WebSockets"])

@router.websocket("/events/{event_id}/availability")
async def websocket_event_availability(
    websocket: WebSocket,
    event_id: int,
    db: Session = Depends(get_db)
):
    await manager.connect_availability(event_id, websocket)
    # Send initial availability state on connection
    try:
        avail = get_event_availability(db, event_id)
        await websocket.send_json({
            "event_id": event_id,
            "total_capacity": avail["total_capacity"],
            "tickets_sold": avail["tickets_sold"],
            "available_tickets": avail["available_tickets"],
            "type": "initial_state"
        })
    except Exception as e:
        logger.warning(f"Error fetching initial availability for event {event_id}: {e}")

    try:
        while True:
            # Keep connection alive, listen for ping or client message
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect_availability(event_id, websocket)
    except Exception as e:
        logger.warning(f"WebSocket error on event {event_id}: {e}")
        manager.disconnect_availability(event_id, websocket)

@router.websocket("/events/{event_id}/updates")
async def websocket_event_updates(websocket: WebSocket, event_id: int):
    await manager.connect_updates(event_id, websocket)
    await websocket.send_json({
        "event_id": event_id,
        "message": "Connected to live event announcements",
        "type": "connected"
    })
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect_updates(event_id, websocket)
    except Exception as e:
        logger.warning(f"WebSocket error on updates for event {event_id}: {e}")
        manager.disconnect_updates(event_id, websocket)
