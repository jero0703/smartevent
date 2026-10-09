from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from app.core.database import get_db
from app.models.user import User
from app.models.event import Event
from app.models.booking import Booking
from app.schemas.admin import (
    UserRoleUpdate, AdminUserResponse, AnalyticsOverviewResponse,
    DailySalesResponse, MonthlyBookingsResponse, PopularEventResponse, TopRevenueEventResponse,
    EventStatusUpdate
)
from app.schemas.event import EventResponse
from app.schemas.booking import BookingResponse, PaginatedBookingResponse
from app.utils.dependencies import require_admin
from app.services.analytics_service import (
    get_admin_overview, get_admin_daily_sales, get_admin_monthly_bookings,
    get_admin_popular_events, get_admin_top_revenue_events
)

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.get("/users", response_model=List[AdminUserResponse])
def get_users(db: Session = Depends(get_db), current_admin: User = Depends(require_admin), page: int = Query(1, ge=1), limit: int = Query(10, ge=1)):
    return db.query(User).offset((page - 1) * limit).limit(limit).all()

@router.get("/users/{user_id}", response_model=AdminUserResponse)
def get_user(user_id: int, db: Session = Depends(get_db), current_admin: User = Depends(require_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.patch("/users/{user_id}/role", response_model=AdminUserResponse)
def update_user_role(user_id: int, role_update: UserRoleUpdate, db: Session = Depends(get_db), current_admin: User = Depends(require_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.role = role_update.role
    db.commit()
    db.refresh(user)
    return user

@router.get("/events", response_model=List[EventResponse])
def get_all_events(db: Session = Depends(get_db), current_admin: User = Depends(require_admin), page: int = Query(1, ge=1), limit: int = Query(10, ge=1)):
    return db.query(Event).offset((page - 1) * limit).limit(limit).all()

@router.get("/events/{event_id}", response_model=EventResponse)
def get_event(event_id: int, db: Session = Depends(get_db), current_admin: User = Depends(require_admin)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event

@router.patch("/events/{event_id}/status", response_model=EventResponse)
def update_event_status_admin(event_id: int, status_update: EventStatusUpdate, db: Session = Depends(get_db), current_admin: User = Depends(require_admin)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    event.event_status = status_update.event_status
    db.commit()
    db.refresh(event)
    return event

@router.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(event_id: int, db: Session = Depends(get_db), current_admin: User = Depends(require_admin)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    db.delete(event)
    db.commit()

@router.get("/bookings", response_model=PaginatedBookingResponse)
def get_all_bookings(db: Session = Depends(get_db), current_admin: User = Depends(require_admin), page: int = Query(1, ge=1), limit: int = Query(10, ge=1)):
    query = db.query(Booking)
    total = query.count()
    pages = (total + limit - 1) // limit
    bookings = query.offset((page - 1) * limit).limit(limit).all()
    return {"items": bookings, "page": page, "limit": limit, "total": total, "pages": pages}

@router.get("/bookings/{booking_id}", response_model=BookingResponse)
def get_booking(booking_id: int, db: Session = Depends(get_db), current_admin: User = Depends(require_admin)):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking

@router.get("/analytics/overview", response_model=AnalyticsOverviewResponse)
def get_overview(db: Session = Depends(get_db), current_admin: User = Depends(require_admin)):
    return get_admin_overview(db)

@router.get("/analytics/daily-sales", response_model=List[DailySalesResponse])
def get_daily_sales(start_date: Optional[date] = None, end_date: Optional[date] = None, db: Session = Depends(get_db), current_admin: User = Depends(require_admin)):
    if start_date and end_date and start_date > end_date:
        raise HTTPException(status_code=400, detail="Invalid date range")
    return get_admin_daily_sales(db, start_date, end_date)

@router.get("/analytics/monthly-bookings", response_model=List[MonthlyBookingsResponse])
def get_monthly_bookings(start_date: Optional[date] = None, end_date: Optional[date] = None, db: Session = Depends(get_db), current_admin: User = Depends(require_admin)):
    if start_date and end_date and start_date > end_date:
        raise HTTPException(status_code=400, detail="Invalid date range")
    return get_admin_monthly_bookings(db, start_date, end_date)

@router.get("/analytics/popular-events", response_model=List[PopularEventResponse])
def get_popular_events(limit: int = 10, db: Session = Depends(get_db), current_admin: User = Depends(require_admin)):
    return get_admin_popular_events(db, limit)

@router.get("/analytics/top-revenue-events", response_model=List[TopRevenueEventResponse])
def get_top_revenue_events(limit: int = 10, db: Session = Depends(get_db), current_admin: User = Depends(require_admin)):
    return get_admin_top_revenue_events(db, limit)
