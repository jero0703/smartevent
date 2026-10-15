from sqlalchemy.orm import Session
from sqlalchemy import func, desc, or_
from typing import Optional, List
from datetime import datetime
from app.models.event import Event, EventCategory, EventStatus
from app.models.booking import Booking, BookingStatus
from app.models.event_view import EventView
from app.models.user import User

def get_trending_events_service(
    db: Session,
    page: int = 1,
    limit: int = 10
) -> dict:
    now = datetime.now()
    tickets_sold_col = func.coalesce(func.sum(Booking.ticket_quantity), 0).label("tickets_sold")

    query = db.query(Event).filter(
        Event.event_status != EventStatus.CANCELLED,
        Event.event_status != EventStatus.COMPLETED,
        Event.event_date >= now
    ).outerjoin(
        Booking,
        (Booking.event_id == Event.id) & (Booking.booking_status == BookingStatus.CONFIRMED)
    ).group_by(Event.id).order_by(tickets_sold_col.desc(), Event.id.desc())

    total = query.count()
    pages = (total + limit - 1) // limit if total > 0 else 0
    items = query.offset((page - 1) * limit).limit(limit).all()

    return {
        "items": items,
        "page": page,
        "limit": limit,
        "total": total,
        "pages": pages,
        "total_pages": pages
    }

def get_similar_events_service(
    db: Session,
    event_id: int,
    page: int = 1,
    limit: int = 10
) -> dict:
    target_event = db.query(Event).filter(Event.id == event_id).first()
    if not target_event:
        return {"items": [], "page": page, "limit": limit, "total": 0, "pages": 0, "total_pages": 0}

    now = datetime.now()
    query = db.query(Event).filter(
        Event.id != event_id,
        Event.category == target_event.category,
        Event.event_status != EventStatus.CANCELLED,
        Event.event_status != EventStatus.COMPLETED,
        Event.event_date >= now
    ).order_by(Event.event_date.asc())

    total = query.count()
    pages = (total + limit - 1) // limit if total > 0 else 0
    items = query.offset((page - 1) * limit).limit(limit).all()

    return {
        "items": items,
        "page": page,
        "limit": limit,
        "total": total,
        "pages": pages,
        "total_pages": pages
    }

def get_personalized_recommendations_service(
    db: Session,
    user: User,
    category: Optional[EventCategory] = None,
    location: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    page: int = 1,
    limit: int = 10
) -> dict:
    now = datetime.now()

    # Base filter: upcoming, not cancelled/completed
    base_filters = [
        Event.event_status != EventStatus.CANCELLED,
        Event.event_status != EventStatus.COMPLETED,
        Event.event_date >= now
    ]

    if category:
        base_filters.append(Event.category == category)
    if location:
        base_filters.append(Event.location.ilike(f"%{location}%"))
    if start_date:
        base_filters.append(Event.event_date >= start_date)
    if end_date:
        base_filters.append(Event.event_date <= end_date)

    # 1. Gather user's preferred categories from bookings and views
    booked_categories = db.query(Event.category).join(
        Booking, Booking.event_id == Event.id
    ).filter(
        Booking.user_id == user.id,
        Booking.booking_status == BookingStatus.CONFIRMED
    ).group_by(Event.category).all()

    viewed_categories = db.query(Event.category).join(
        EventView, EventView.event_id == Event.id
    ).filter(
        EventView.user_id == user.id
    ).group_by(Event.category).all()

    preferred_categories = list(set([c[0] for c in (booked_categories + viewed_categories)]))

    user_location = user.location

    # If user has preferred categories or location, prioritize them
    tickets_sold_col = func.coalesce(func.sum(Booking.ticket_quantity), 0).label("tickets_sold")

    query = db.query(Event).filter(*base_filters).outerjoin(
        Booking,
        (Booking.event_id == Event.id) & (Booking.booking_status == BookingStatus.CONFIRMED)
    ).group_by(Event.id)

    if preferred_categories:
        # Match preferred categories first
        category_order = Event.category.in_(preferred_categories)
        if user_location:
            location_match = Event.location.ilike(f"%{user_location}%")
            query = query.order_by(
                location_match.desc(),
                category_order.desc(),
                tickets_sold_col.desc(),
                Event.event_date.asc()
            )
        else:
            query = query.order_by(
                category_order.desc(),
                tickets_sold_col.desc(),
                Event.event_date.asc()
            )
    elif user_location:
        location_match = Event.location.ilike(f"%{user_location}%")
        query = query.order_by(
            location_match.desc(),
            tickets_sold_col.desc(),
            Event.event_date.asc()
        )
    else:
        # Fallback for new user: rank by popularity and upcoming date
        query = query.order_by(tickets_sold_col.desc(), Event.event_date.asc())

    total = query.count()
    pages = (total + limit - 1) // limit if total > 0 else 0
    items = query.offset((page - 1) * limit).limit(limit).all()

    return {
        "items": items,
        "page": page,
        "limit": limit,
        "total": total,
        "pages": pages,
        "total_pages": pages
    }
