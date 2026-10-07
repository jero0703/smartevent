from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.models.booking import Booking
from app.schemas.booking import BookingCreate, BookingResponse, PaginatedBookingResponse
from app.services.auth_service import get_current_user
from app.services.booking_service import create_booking, cancel_booking

router = APIRouter(prefix="/bookings", tags=["Bookings"])

@router.post("", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
def book_event(
    booking_in: BookingCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return create_booking(db=db, user_id=current_user.id, booking_in=booking_in)

@router.get("/my", response_model=PaginatedBookingResponse)
def get_my_bookings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100)
):
    query = db.query(Booking).filter(Booking.user_id == current_user.id)
    total = query.count()
    pages = (total + limit - 1) // limit
    bookings = query.offset((page - 1) * limit).limit(limit).all()
    
    return {
        "items": bookings,
        "page": page,
        "limit": limit,
        "total": total,
        "pages": pages
    }

@router.get("/{booking_id}", response_model=BookingResponse)
def get_booking_details(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this booking")
    return booking

@router.patch("/{booking_id}/cancel", response_model=BookingResponse)
def cancel_my_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return cancel_booking(db=db, booking_id=booking_id, user_id=current_user.id)
