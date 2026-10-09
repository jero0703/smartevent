from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date
from typing import Optional
from app.models.user import User, UserRole
from app.models.event import Event
from app.models.booking import Booking, BookingStatus

def get_admin_overview(db: Session):
    total_users = db.query(func.count(User.id)).filter(User.role == UserRole.USER).scalar() or 0
    total_organizers = db.query(func.count(User.id)).filter(User.role == UserRole.ORGANIZER).scalar() or 0
    total_events = db.query(func.count(Event.id)).scalar() or 0
    
    confirmed_bookings = db.query(Booking).filter(Booking.booking_status == BookingStatus.CONFIRMED)
    total_bookings = confirmed_bookings.count()
    total_tickets_sold = confirmed_bookings.with_entities(func.sum(Booking.ticket_quantity)).scalar() or 0
    total_revenue = confirmed_bookings.with_entities(func.sum(Booking.total_price)).scalar() or 0.0

    return {
        "total_users": total_users,
        "total_organizers": total_organizers,
        "total_events": total_events,
        "total_bookings": total_bookings,
        "total_tickets_sold": int(total_tickets_sold),
        "total_revenue": float(total_revenue)
    }

def get_admin_daily_sales(db: Session, start_date: Optional[date] = None, end_date: Optional[date] = None):
    query = db.query(
        func.date(Booking.created_at).label('date'),
        func.sum(Booking.ticket_quantity).label('tickets_sold'),
        func.sum(Booking.total_price).label('revenue')
    ).filter(Booking.booking_status == BookingStatus.CONFIRMED)
    
    if start_date:
        query = query.filter(func.date(Booking.created_at) >= start_date)
    if end_date:
        query = query.filter(func.date(Booking.created_at) <= end_date)
        
    query = query.group_by(func.date(Booking.created_at)).order_by(func.date(Booking.created_at))
    
    results = []
    for row in query.all():
        results.append({
            "date": str(row.date),
            "tickets_sold": int(row.tickets_sold or 0),
            "revenue": float(row.revenue or 0.0)
        })
    return results

def get_admin_monthly_bookings(db: Session, start_date: Optional[date] = None, end_date: Optional[date] = None):
    query = db.query(
        func.strftime('%Y-%m', Booking.created_at).label('month'),
        func.count(Booking.id).label('booking_count')
    ).filter(Booking.booking_status == BookingStatus.CONFIRMED)
    
    if start_date:
        query = query.filter(func.date(Booking.created_at) >= start_date)
    if end_date:
        query = query.filter(func.date(Booking.created_at) <= end_date)
        
    query = query.group_by('month').order_by('month')
    
    results = []
    for row in query.all():
        results.append({
            "month": row.month,
            "booking_count": row.booking_count
        })
    return results

def get_admin_popular_events(db: Session, limit: int = 10):
    query = db.query(
        Event.id,
        Event.title,
        func.sum(Booking.ticket_quantity).label('tickets_sold'),
        func.count(Booking.id).label('booking_count')
    ).join(Booking).filter(Booking.booking_status == BookingStatus.CONFIRMED)\
    .group_by(Event.id)\
    .order_by(func.sum(Booking.ticket_quantity).desc())\
    .limit(limit)
    
    results = []
    for row in query.all():
        results.append({
            "event_id": row.id,
            "event_title": row.title,
            "tickets_sold": int(row.tickets_sold or 0),
            "booking_count": int(row.booking_count or 0)
        })
    return results

def get_admin_top_revenue_events(db: Session, limit: int = 10):
    query = db.query(
        Event.id,
        Event.title,
        func.sum(Booking.ticket_quantity).label('tickets_sold'),
        func.sum(Booking.total_price).label('revenue')
    ).join(Booking).filter(Booking.booking_status == BookingStatus.CONFIRMED)\
    .group_by(Event.id)\
    .order_by(func.sum(Booking.total_price).desc())\
    .limit(limit)
    
    results = []
    for row in query.all():
        results.append({
            "event_id": row.id,
            "event_title": row.title,
            "tickets_sold": int(row.tickets_sold or 0),
            "revenue": float(row.revenue or 0.0)
        })
    return results
