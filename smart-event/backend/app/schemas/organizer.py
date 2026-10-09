from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.models.event import EventCategory, EventStatus
from app.schemas.event import EventResponse

class EventCreate(BaseModel):
    title: str
    description: Optional[str] = None
    category: EventCategory
    location: str
    event_date: datetime
    ticket_price: float
    total_tickets: int
    banner_image: Optional[str] = None

class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[EventCategory] = None
    location: Optional[str] = None
    event_date: Optional[datetime] = None
    ticket_price: Optional[float] = None
    total_tickets: Optional[int] = None
    banner_image: Optional[str] = None

class OrganizerAnalyticsOverview(BaseModel):
    total_events: int
    total_bookings: int
    total_tickets_sold: int
    total_remaining_tickets: int
    total_revenue: float

class OrganizerEventAnalytics(BaseModel):
    event_id: int
    event_title: str
    total_tickets: int
    tickets_sold: int
    remaining_tickets: int
    booking_count: int
    revenue: float
