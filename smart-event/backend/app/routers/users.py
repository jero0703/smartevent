from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from app.core.database import get_db
from app.schemas.user import (
    UserResponse,
    UserUpdate,
    UserBookingSummaryResponse,
    UserActivityResponse,
    UserRecentViewResponse
)
from app.models.user import User
from app.models.booking import Booking, BookingStatus
from app.models.event import Event, EventStatus
from app.models.wishlist import Wishlist
from app.models.review import Review
from app.models.event_view import EventView
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.patch("/me", response_model=UserResponse)
def update_users_me(
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    update_data = user_in.model_dump(exclude_unset=True)
    
    # Strictly forbid sensitive fields (even if passed)
    forbidden_fields = {"role", "id", "hashed_password", "email", "created_at"}
    for field in forbidden_fields:
        update_data.pop(field, None)

    for field, value in update_data.items():
        setattr(current_user, field, value)

    db.commit()
    db.refresh(current_user)
    return current_user

@router.get("/me/booking-summary", response_model=UserBookingSummaryResponse)
def get_user_booking_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user_bookings = db.query(Booking).filter(Booking.user_id == current_user.id).all()

    total_bookings = len(user_bookings)
    confirmed_bookings = sum(1 for b in user_bookings if b.booking_status == BookingStatus.CONFIRMED)
    pending_bookings = sum(1 for b in user_bookings if b.booking_status == BookingStatus.PENDING)
    cancelled_bookings = sum(1 for b in user_bookings if b.booking_status == BookingStatus.CANCELLED)

    total_tickets = sum(b.ticket_quantity for b in user_bookings if b.booking_status == BookingStatus.CONFIRMED)
    total_spent = sum(float(b.final_amount if b.final_amount is not None else b.total_price) for b in user_bookings if b.booking_status == BookingStatus.CONFIRMED)

    # Upcoming events from confirmed bookings
    now = datetime.now()
    upcoming_events_map = {}
    for b in user_bookings:
        if b.booking_status == BookingStatus.CONFIRMED and b.event:
            if b.event.event_status != EventStatus.CANCELLED and b.event.event_date >= now:
                upcoming_events_map[b.event.id] = b.event

    return {
        "total_bookings": total_bookings,
        "confirmed_bookings": confirmed_bookings,
        "pending_bookings": pending_bookings,
        "cancelled_bookings": cancelled_bookings,
        "total_tickets_booked": total_tickets,
        "total_spent": round(total_spent, 2),
        "upcoming_events": list(upcoming_events_map.values())
    }

@router.get("/me/activity", response_model=UserActivityResponse)
def get_user_activity(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Recent views (latest 10)
    views = db.query(EventView).filter(
        EventView.user_id == current_user.id
    ).order_by(EventView.viewed_at.desc()).limit(10).all()

    recent_views = []
    seen_events = set()
    for v in views:
        if v.event and v.event_id not in seen_events:
            seen_events.add(v.event_id)
            recent_views.append(UserRecentViewResponse(
                event_id=v.event.id,
                title=v.event.title,
                category=v.event.category,
                location=v.event.location,
                viewed_at=v.viewed_at
            ))

    wishlist_count = db.query(Wishlist).filter(Wishlist.user_id == current_user.id).count()
    total_reviews = db.query(Review).filter(Review.user_id == current_user.id).count()

    return {
        "user_id": current_user.id,
        "recent_views": recent_views,
        "wishlist_count": wishlist_count,
        "total_reviews": total_reviews
    }
