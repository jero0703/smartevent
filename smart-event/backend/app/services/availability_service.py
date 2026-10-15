from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status
from app.models.event import Event
from app.models.booking import Booking, BookingStatus
from app.utils.websocket_manager import notify_availability_sync

def get_event_availability(db: Session, event_id: int) -> dict:
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )

    # Confirmed tickets sold
    tickets_sold = db.query(func.coalesce(func.sum(Booking.ticket_quantity), 0)).filter(
        Booking.event_id == event_id,
        Booking.booking_status == BookingStatus.CONFIRMED
    ).scalar() or 0

    return {
        "event_id": event.id,
        "total_capacity": event.total_tickets,
        "tickets_sold": int(tickets_sold),
        "available_tickets": event.available_tickets
    }

def broadcast_current_availability(db: Session, event_id: int):
    avail = get_event_availability(db, event_id)
    notify_availability_sync(
        event_id=event_id,
        total_capacity=avail["total_capacity"],
        tickets_sold=avail["tickets_sold"],
        available_tickets=avail["available_tickets"]
    )
