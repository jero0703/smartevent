from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime, date
from app.models.user import UserRole
from app.models.event import EventStatus

# User Management
class UserRoleUpdate(BaseModel):
    role: UserRole

class AdminUserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    role: UserRole
    created_at: datetime

    class Config:
        from_attributes = True

# Analytics
class AnalyticsOverviewResponse(BaseModel):
    total_users: int
    total_organizers: int
    total_events: int
    total_bookings: int
    total_tickets_sold: int
    total_revenue: float

class DailySalesResponse(BaseModel):
    date: str
    tickets_sold: int
    revenue: float

class MonthlyBookingsResponse(BaseModel):
    month: str
    booking_count: int

class PopularEventResponse(BaseModel):
    event_id: int
    event_title: str
    tickets_sold: int
    booking_count: int

class TopRevenueEventResponse(BaseModel):
    event_id: int
    event_title: str
    tickets_sold: int
    revenue: float

# Event Status
class EventStatusUpdate(BaseModel):
    event_status: EventStatus
