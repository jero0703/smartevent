from sqlalchemy import Column, Integer, String, Text, Enum as SQLEnum, DateTime, DECIMAL, CheckConstraint, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum

class EventCategory(str, enum.Enum):
    Music = "Music"
    Tech = "Tech"
    Sports = "Sports"
    Business = "Business"

class EventStatus(str, enum.Enum):
    UPCOMING = "UPCOMING"
    ONGOING = "ONGOING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    category = Column(SQLEnum(EventCategory), nullable=False)
    location = Column(String(255), nullable=False)
    event_date = Column(DateTime, nullable=False, index=True)
    ticket_price = Column(DECIMAL(10, 2), nullable=False)
    total_tickets = Column(Integer, nullable=False)
    available_tickets = Column(Integer, nullable=False)
    banner_image = Column(String(255))
    organizer_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    event_status = Column(SQLEnum(EventStatus), default=EventStatus.UPCOMING, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now())

    organizer = relationship("User", back_populates="events")
    bookings = relationship("Booking", back_populates="event", cascade="all, delete")
    reviews = relationship("Review", back_populates="event", cascade="all, delete")
    wishlists = relationship("Wishlist", back_populates="event", cascade="all, delete")
    updates = relationship("EventUpdate", back_populates="event", cascade="all, delete")
    views = relationship("EventView", back_populates="event", cascade="all, delete")

    __table_args__ = (
        CheckConstraint('ticket_price >= 0', name='check_ticket_price_positive'),
        CheckConstraint('total_tickets > 0', name='check_total_tickets_positive'),
        CheckConstraint('available_tickets >= 0', name='check_available_tickets_positive'),
        CheckConstraint('available_tickets <= total_tickets', name='check_available_le_total')
    )
