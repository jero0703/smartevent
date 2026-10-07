from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False)
    ticket_code = Column(String(100), unique=True, index=True, nullable=False)
    qr_code_url = Column(String(255), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    booking = relationship("Booking", back_populates="ticket")
