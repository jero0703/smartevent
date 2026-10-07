from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.models.ticket import Ticket
from app.schemas.ticket import TicketDetailResponse, TicketVerificationResponse
from app.services.auth_service import get_current_user
from app.services.ticket_service import verify_ticket

router = APIRouter(prefix="/tickets", tags=["Tickets"])

@router.get("/my", response_model=list[TicketDetailResponse])
def get_my_tickets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Retrieve tickets associated with the user's bookings
    tickets = db.query(Ticket).join(Ticket.booking).filter(Ticket.booking.has(user_id=current_user.id)).all()
    
    response = []
    for t in tickets:
        response.append({
            "id": t.id,
            "ticket_code": t.ticket_code,
            "qr_code_url": t.qr_code_url,
            "booking_id": t.booking_id,
            "created_at": t.created_at,
            "event": t.booking.event,
            "ticket_quantity": t.booking.ticket_quantity,
            "booking_status": t.booking.booking_status
        })
    return response

@router.get("/verify/{ticket_code}", response_model=TicketVerificationResponse)
def verify_ticket_endpoint(
    ticket_code: str,
    db: Session = Depends(get_db)
):
    return verify_ticket(db, ticket_code)
