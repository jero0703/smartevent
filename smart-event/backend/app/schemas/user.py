from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from app.models.user import UserRole
from typing import Optional, List
from app.schemas.event import EventResponse

class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str
    role: Optional[UserRole] = UserRole.USER

class UserUpdate(BaseModel):
    phone_number: Optional[str] = Field(None, max_length=20)
    location: Optional[str] = Field(None, max_length=100)
    full_name: Optional[str] = Field(None, max_length=100)
    bio: Optional[str] = Field(None, max_length=500)

class UserResponse(UserBase):
    id: int
    role: UserRole
    phone_number: Optional[str] = None
    location: Optional[str] = None
    full_name: Optional[str] = None
    bio: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}

class UserBookingSummaryResponse(BaseModel):
    total_bookings: int
    confirmed_bookings: int
    pending_bookings: int
    cancelled_bookings: int
    total_tickets_booked: int
    total_spent: float
    upcoming_events: List[EventResponse]

class UserRecentViewResponse(BaseModel):
    event_id: int
    title: str
    category: str
    location: str
    viewed_at: datetime

class UserActivityResponse(BaseModel):
    user_id: int
    recent_views: List[UserRecentViewResponse]
    wishlist_count: int
    total_reviews: int
