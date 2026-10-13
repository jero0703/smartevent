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

from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from typing import Optional
from app.core.config import settings

optional_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)

def get_optional_user(token: Optional[str] = Depends(optional_oauth2_scheme), db: Session = Depends(get_db)) -> Optional[User]:
    if not token:
        return None
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            return None
        return db.query(User).filter(User.id == int(user_id)).first()
    except Exception:
        return None

@router.get("/verify/{ticket_code}", response_model=TicketVerificationResponse)
def verify_ticket_endpoint(
    ticket_code: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    ticket = db.query(Ticket).filter(Ticket.ticket_code == ticket_code).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
        
    from app.models.user import UserRole
    if current_user and current_user.role == UserRole.ORGANIZER:
        if ticket.booking.event.organizer_id != current_user.id:
            raise HTTPException(status_code=403, detail="You can only verify tickets for your own events")
            
    return verify_ticket(db, ticket_code)
