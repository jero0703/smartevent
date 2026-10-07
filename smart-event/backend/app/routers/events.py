from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from app.core.database import get_db
from app.models.event import Event, EventCategory
from app.schemas.event import EventResponse, PaginatedEventResponse

router = APIRouter(prefix="/events", tags=["Events"])

@router.get("", response_model=PaginatedEventResponse)
def get_events(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    category: Optional[EventCategory] = None
):
    query = db.query(Event)
    
    if search:
        query = query.filter(Event.title.ilike(f"%{search}%"))
        
    if category:
        query = query.filter(Event.category == category)
        
    total = query.count()
    pages = (total + limit - 1) // limit
    
    events = query.offset((page - 1) * limit).limit(limit).all()
    
    return {
        "items": events,
        "page": page,
        "limit": limit,
        "total": total,
        "pages": pages
    }

@router.get("/{event_id}", response_model=EventResponse)
def get_event(event_id: int, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event
