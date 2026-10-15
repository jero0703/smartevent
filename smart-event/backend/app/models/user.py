from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum

class UserRole(str, enum.Enum):
    USER = "USER"
    ORGANIZER = "ORGANIZER"
    ADMIN = "ADMIN"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.USER, nullable=False)
    phone_number = Column(String(20), nullable=True)
    location = Column(String(100), nullable=True)
    full_name = Column(String(100), nullable=True)
    bio = Column(String(500), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    events = relationship("Event", back_populates="organizer")
    bookings = relationship("Booking", back_populates="user", cascade="all, delete")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete")
    reviews = relationship("Review", back_populates="user", cascade="all, delete")
    wishlists = relationship("Wishlist", back_populates="user", cascade="all, delete")
    event_views = relationship("EventView", back_populates="user", cascade="all, delete")
    chat_history = relationship("ChatHistory", back_populates="user", cascade="all, delete")
