from pydantic import BaseModel
from datetime import datetime
from app.schemas.event import EventResponse
from app.models.booking import BookingStatus

class TicketBase(BaseModel):
    ticket_code: str
    qr_code_url: str

class TicketResponse(TicketBase):
    id: int
    booking_id: int
    created_at: datetime

    model_config = {"from_attributes": True}

class TicketDetailResponse(TicketResponse):
    event: EventResponse
    ticket_quantity: int
    booking_status: BookingStatus

class TicketVerificationResponse(BaseModel):
    valid: bool
    ticket_code: str | None = None
    event: str | None = None
    booking_id: int | None = None
    status: BookingStatus | None = None
