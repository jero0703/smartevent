from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from app.core.database import get_db
from app.models.user import User
from app.models.event import Event, EventStatus
from app.models.booking import Booking, BookingStatus
from app.models.notification import NotificationType
from app.schemas.event import EventResponse
from app.schemas.organizer import EventCreate, EventUpdate, OrganizerAnalyticsOverview, OrganizerEventAnalytics
from app.schemas.booking import BookingResponse
from app.utils.dependencies import require_organizer
from app.services.notification_service import create_notification

router = APIRouter(prefix="/organizer", tags=["Organizer"])

@router.post("/events", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
def create_organizer_event(event_in: EventCreate, db: Session = Depends(get_db), current_org: User = Depends(require_organizer)):
    event = Event(
        title=event_in.title,
        description=event_in.description,
        category=event_in.category,
        location=event_in.location,
        event_date=event_in.event_date,
        ticket_price=event_in.ticket_price,
        total_tickets=event_in.total_tickets,
        available_tickets=event_in.total_tickets,
        banner_image=event_in.banner_image,
        organizer_id=current_org.id,
        event_status=EventStatus.UPCOMING
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event

@router.get("/events", response_model=List[EventResponse])
def get_organizer_events(db: Session = Depends(get_db), current_org: User = Depends(require_organizer)):
    return db.query(Event).filter(Event.organizer_id == current_org.id).all()

@router.get("/events/{event_id}", response_model=EventResponse)
def get_organizer_event(event_id: int, db: Session = Depends(get_db), current_org: User = Depends(require_organizer)):
    event = db.query(Event).filter(Event.id == event_id, Event.organizer_id == current_org.id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found or not owned by you")
    return event

@router.put("/events/{event_id}", response_model=EventResponse)
def update_organizer_event(event_id: int, event_update: EventUpdate, db: Session = Depends(get_db), current_org: User = Depends(require_organizer)):
    event = db.query(Event).filter(Event.id == event_id, Event.organizer_id == current_org.id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found or not owned by you")
        
    update_data = event_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(event, key, value)
        
    # Notify users with confirmed bookings
    bookings = db.query(Booking).filter(Booking.event_id == event.id, Booking.booking_status == BookingStatus.CONFIRMED).all()
    for b in bookings:
        create_notification(
            db=db,
            user_id=b.user_id,
            title="Event Updated",
            message="The details of your booked event have been updated.",
            type=NotificationType.EVENT
        )
    
    db.commit()
    db.refresh(event)
    return event

@router.patch("/events/{event_id}/cancel", response_model=EventResponse)
def cancel_organizer_event(event_id: int, db: Session = Depends(get_db), current_org: User = Depends(require_organizer)):
    event = db.query(Event).filter(Event.id == event_id, Event.organizer_id == current_org.id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found or not owned by you")
        
    if event.event_status == EventStatus.CANCELLED:
        raise HTTPException(status_code=400, detail="Event has already been cancelled.")
        
    event.event_status = EventStatus.CANCELLED
    
    # Notify users with confirmed bookings
    bookings = db.query(Booking).filter(Booking.event_id == event.id, Booking.booking_status == BookingStatus.CONFIRMED).all()
    for b in bookings:
        create_notification(
            db=db,
            user_id=b.user_id,
            title="Event Cancelled",
            message=f'The event "{event.title}" has been cancelled.',
            type=NotificationType.EVENT
        )
        
    db.commit()
    db.refresh(event)
    return event

@router.get("/events/{event_id}/bookings", response_model=List[BookingResponse])
def get_event_bookings(event_id: int, db: Session = Depends(get_db), current_org: User = Depends(require_organizer)):
    event = db.query(Event).filter(Event.id == event_id, Event.organizer_id == current_org.id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found or not owned by you")
    return db.query(Booking).filter(Booking.event_id == event_id).all()

@router.get("/analytics", response_model=OrganizerAnalyticsOverview)
def get_organizer_analytics(db: Session = Depends(get_db), current_org: User = Depends(require_organizer)):
    events = db.query(Event).filter(Event.organizer_id == current_org.id).all()
    event_ids = [e.id for e in events]
    
    total_events = len(events)
    total_remaining_tickets = sum(e.available_tickets for e in events)
    
    if not event_ids:
        return OrganizerAnalyticsOverview(
            total_events=0, total_bookings=0, total_tickets_sold=0,
            total_remaining_tickets=0, total_revenue=0.0
        )
        
    confirmed_bookings = db.query(Booking).filter(
        Booking.event_id.in_(event_ids),
        Booking.booking_status == BookingStatus.CONFIRMED
    )
    
    total_bookings = confirmed_bookings.count()
    total_tickets_sold = confirmed_bookings.with_entities(func.sum(Booking.ticket_quantity)).scalar() or 0
    total_revenue = confirmed_bookings.with_entities(func.sum(Booking.total_price)).scalar() or 0.0
    
    return OrganizerAnalyticsOverview(
        total_events=total_events,
        total_bookings=total_bookings,
        total_tickets_sold=int(total_tickets_sold),
        total_remaining_tickets=total_remaining_tickets,
        total_revenue=float(total_revenue)
    )

@router.get("/analytics/events", response_model=List[OrganizerEventAnalytics])
def get_organizer_event_analytics(db: Session = Depends(get_db), current_org: User = Depends(require_organizer)):
    events = db.query(Event).filter(Event.organizer_id == current_org.id).all()
    results = []
    
    for event in events:
        confirmed_bookings = db.query(Booking).filter(
            Booking.event_id == event.id,
            Booking.booking_status == BookingStatus.CONFIRMED
        )
        
        booking_count = confirmed_bookings.count()
        tickets_sold = confirmed_bookings.with_entities(func.sum(Booking.ticket_quantity)).scalar() or 0
        revenue = confirmed_bookings.with_entities(func.sum(Booking.total_price)).scalar() or 0.0
        
        results.append(OrganizerEventAnalytics(
            event_id=event.id,
            event_title=event.title,
            total_tickets=event.total_tickets,
            tickets_sold=int(tickets_sold),
            remaining_tickets=event.available_tickets,
            booking_count=booking_count,
            revenue=float(revenue)
        ))
        
    return results
