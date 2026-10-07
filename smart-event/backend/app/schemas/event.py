from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from app.models.event import EventCategory

class EventBase(BaseModel):
    title: str = Field(..., min_length=1)
    description: Optional[str] = None
    category: EventCategory
    location: str
    event_date: datetime
    ticket_price: float = Field(..., ge=0)
    total_tickets: int = Field(..., gt=0)
    available_tickets: int = Field(..., ge=0)
    banner_image: Optional[str] = None

class EventCreate(EventBase):
    pass

class EventResponse(EventBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}

class PaginatedEventResponse(BaseModel):
    items: list[EventResponse]
    page: int
    limit: int
    total: int
    pages: int
