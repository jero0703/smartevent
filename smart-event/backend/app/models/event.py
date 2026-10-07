from sqlalchemy import Column, Integer, String, Text, Enum as SQLEnum, DateTime, DECIMAL, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum

class EventCategory(str, enum.Enum):
    Music = "Music"
    Tech = "Tech"
    Sports = "Sports"
    Business = "Business"

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    category = Column(SQLEnum(EventCategory), nullable=False)
    location = Column(String(255), nullable=False)
    event_date = Column(DateTime, nullable=False)
    ticket_price = Column(DECIMAL(10, 2), nullable=False)
    total_tickets = Column(Integer, nullable=False)
    available_tickets = Column(Integer, nullable=False)
    banner_image = Column(String(255))
    created_at = Column(DateTime, server_default=func.now())

    bookings = relationship("Booking", back_populates="event", cascade="all, delete")

    __table_args__ = (
        CheckConstraint('ticket_price >= 0', name='check_ticket_price_positive'),
        CheckConstraint('total_tickets > 0', name='check_total_tickets_positive'),
        CheckConstraint('available_tickets >= 0', name='check_available_tickets_positive'),
        CheckConstraint('available_tickets <= total_tickets', name='check_available_le_total')
    )
