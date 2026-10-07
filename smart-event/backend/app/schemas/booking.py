from pydantic import BaseModel, Field
from datetime import datetime
from app.models.booking import BookingStatus
from app.schemas.event import EventResponse

class BookingBase(BaseModel):
    event_id: int
    ticket_quantity: int = Field(..., gt=0)

class BookingCreate(BookingBase):
    pass

class BookingResponse(BookingBase):
    id: int
    user_id: int
    total_price: float
    booking_status: BookingStatus
    created_at: datetime
    event: EventResponse

    model_config = {"from_attributes": True}

class PaginatedBookingResponse(BaseModel):
    items: list[BookingResponse]
    page: int
    limit: int
    total: int
    pages: int
