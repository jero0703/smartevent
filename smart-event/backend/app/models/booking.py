from sqlalchemy import Column, Integer, DECIMAL, Enum as SQLEnum, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum

class BookingStatus(str, enum.Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"

class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    ticket_quantity = Column(Integer, nullable=False)
    total_price = Column(DECIMAL(10, 2), nullable=False)
    coupon_id = Column(Integer, ForeignKey("coupons.id", ondelete="SET NULL"), nullable=True, index=True)
    discount_amount = Column(DECIMAL(10, 2), default=0.00, nullable=False)
    final_amount = Column(DECIMAL(10, 2), nullable=False)
    booking_status = Column(SQLEnum(BookingStatus), default=BookingStatus.PENDING, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="bookings")
    event = relationship("Event", back_populates="bookings")
    ticket = relationship("Ticket", back_populates="booking", uselist=False, cascade="all, delete")
    coupon = relationship("Coupon", back_populates="bookings")
    payments = relationship("Payment", back_populates="booking", cascade="all, delete")

    __table_args__ = (
        CheckConstraint('ticket_quantity > 0', name='check_ticket_quantity_positive'),
    )
