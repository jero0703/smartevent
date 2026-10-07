from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.ticket import Ticket
from app.models.booking import Booking, BookingStatus

def verify_ticket(db: Session, ticket_code: str):
    ticket = db.query(Ticket).filter(Ticket.ticket_code == ticket_code).first()
    
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
        
    booking = ticket.booking
    
    return {
        "valid": booking.booking_status == BookingStatus.CONFIRMED,
        "ticket_code": ticket.ticket_code,
        "event": booking.event.title,
        "booking_id": booking.id,
        "status": booking.booking_status
    }
