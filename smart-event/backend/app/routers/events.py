from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import Optional
from datetime import datetime
from app.core.database import get_db
from app.models.event import Event, EventCategory, EventStatus
from app.models.booking import Booking, BookingStatus
from app.schemas.event import EventResponse, PaginatedEventResponse

router = APIRouter(prefix="/events", tags=["Events"])

@router.get("", response_model=PaginatedEventResponse)
def get_events(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    category: Optional[EventCategory] = None,
    location: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    sort_by: Optional[str] = Query("date", pattern="^(date|popularity|price)$"),
    sort_order: Optional[str] = Query("asc", pattern="^(asc|desc)$")
):
    # Validation rules
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date cannot be greater than end_date"
        )

    if min_price is not None and max_price is not None and min_price > max_price:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="min_price cannot be greater than max_price"
        )

    # Exclude cancelled events from public discovery
    filters = [Event.event_status != EventStatus.CANCELLED]

    if search:
        search_term = f"%{search}%"
        filters.append(
            or_(
                Event.title.ilike(search_term),
                Event.description.ilike(search_term)
            )
        )

    if category:
        filters.append(Event.category == category)

    if location:
        filters.append(Event.location.ilike(f"%{location}%"))

    if start_date:
        filters.append(Event.event_date >= start_date)

    if end_date:
        filters.append(Event.event_date <= end_date)

    if min_price is not None:
        filters.append(Event.ticket_price >= min_price)

    if max_price is not None:
        filters.append(Event.ticket_price <= max_price)

    # Total count using base filters
    total = db.query(Event).filter(*filters).count()
    pages = (total + limit - 1) // limit if total > 0 else 0

    query = db.query(Event).filter(*filters)

    # Sorting
    is_desc = sort_order == "desc"
    if sort_by == "popularity":
        tickets_sold_col = func.coalesce(func.sum(Booking.ticket_quantity), 0).label("tickets_sold")
        query = query.outerjoin(
            Booking,
            (Booking.event_id == Event.id) & (Booking.booking_status == BookingStatus.CONFIRMED)
        ).group_by(Event.id)
        if is_desc:
            query = query.order_by(tickets_sold_col.desc(), Event.id.desc())
        else:
            query = query.order_by(tickets_sold_col.asc(), Event.id.asc())
    elif sort_by == "price":
        order_expr = Event.ticket_price.desc() if is_desc else Event.ticket_price.asc()
        query = query.order_by(order_expr, Event.id.asc())
    else:  # sort_by == "date"
        order_expr = Event.event_date.desc() if is_desc else Event.event_date.asc()
        query = query.order_by(order_expr, Event.id.asc())

    events = query.offset((page - 1) * limit).limit(limit).all()

    return {
        "items": events,
        "page": page,
        "limit": limit,
        "total": total,
        "pages": pages,
        "total_pages": pages
    }

@router.get("/{event_id}", response_model=EventResponse)
def get_event(event_id: int, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event
