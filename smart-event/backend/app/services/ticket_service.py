from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.ticket import Ticket
from app.models.booking import Booking, BookingStatus

def verify_ticket(db: Session, ticket_code: str):
    ticket = db.query(Ticket).filter(Ticket.ticket_code == ticket_code).first()
    
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
        
    booking = ticket.booking
    
    from app.models.event import EventStatus
    
    is_valid = booking.booking_status == BookingStatus.CONFIRMED
    if booking.event.event_status == EventStatus.CANCELLED:
        is_valid = False
    
    return {
        "valid": is_valid,
        "ticket_code": ticket.ticket_code,
        "event": booking.event.title,
        "booking_id": booking.id,
        "status": booking.booking_status
    }
