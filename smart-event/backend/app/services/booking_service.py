from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from app.models.booking import Booking, BookingStatus
from app.models.event import Event
from app.models.ticket import Ticket
from app.models.notification import NotificationType
from app.schemas.booking import BookingCreate
from app.services.notification_service import create_notification
from app.utils.qr_generator import generate_qr_code
import uuid

def create_booking(db: Session, user_id: int, booking_in: BookingCreate) -> Booking:
    event = db.query(Event).filter(Event.id == booking_in.event_id).with_for_update().first()
    
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
        
    from app.models.event import EventStatus
    if event.event_status == EventStatus.CANCELLED:
        raise HTTPException(status_code=400, detail="Cannot book a cancelled event")
    if event.event_status == EventStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Cannot book a completed event")
        
    if event.available_tickets < booking_in.ticket_quantity:
        if event.available_tickets == 0:
            raise HTTPException(status_code=400, detail="Event is sold out")
        raise HTTPException(status_code=400, detail="Not enough tickets available")
        
    total_price = event.ticket_price * booking_in.ticket_quantity
    
    # Process optional coupon
    coupon_id = None
    discount_amount = 0.00
    final_amount = total_price

    if booking_in.coupon_code:
        from app.services.coupon_service import validate_coupon_and_calculate_discount
        coupon, discount_amount, final_amount = validate_coupon_and_calculate_discount(
            db=db,
            coupon_code=booking_in.coupon_code,
            booking_amount=float(total_price)
        )
        coupon_id = coupon.id
    
    target_status = booking_in.status if booking_in.status is not None else BookingStatus.CONFIRMED

    booking = Booking(
        user_id=user_id,
        event_id=event.id,
        ticket_quantity=booking_in.ticket_quantity,
        total_price=total_price,
        coupon_id=coupon_id,
        discount_amount=discount_amount,
        final_amount=final_amount,
        booking_status=target_status
    )
    
    db.add(booking)
    event.available_tickets -= booking_in.ticket_quantity
    
    db.flush()
    
    if target_status == BookingStatus.CONFIRMED:
        # Generate Ticket only if booking is confirmed
        ticket_code = f"TKT-{uuid.uuid4().hex[:8].upper()}"
        qr_url = generate_qr_code(ticket_code, booking.id)
        
        ticket = Ticket(
            booking_id=booking.id,
            ticket_code=ticket_code,
            qr_code_url=qr_url
        )
        db.add(ticket)
        
        # Generate Notification
        create_notification(
            db=db,
            user_id=user_id,
            title="Booking Confirmed",
            message=f"Your booking for {event.title} has been confirmed.",
            type=NotificationType.BOOKING
        )
    else:
        create_notification(
            db=db,
            user_id=user_id,
            title="Booking Initiated",
            message=f"Your booking for {event.title} is pending payment.",
            type=NotificationType.BOOKING
        )
    
    try:
        db.commit()
        db.refresh(booking)
        from app.services.availability_service import broadcast_current_availability
        broadcast_current_availability(db, event.id)
        return booking
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Booking failed due to internal error")

def cancel_booking(db: Session, booking_id: int, user_id: int) -> Booking:
    booking = db.query(Booking).filter(Booking.id == booking_id).with_for_update().first()
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
        
    if booking.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to cancel this booking")
        
    if booking.booking_status == BookingStatus.CANCELLED:
        raise HTTPException(status_code=400, detail="Booking is already cancelled")
        
    if booking.booking_status != BookingStatus.CONFIRMED:
        raise HTTPException(status_code=400, detail="Only CONFIRMED bookings can be cancelled")
        
    # Check if event is in the past (basic check, could be expanded)
    from datetime import datetime
    if booking.event.event_date < datetime.now():
         raise HTTPException(status_code=400, detail="Cannot cancel booking for a past event")

    booking.booking_status = BookingStatus.CANCELLED
    
    # Restore tickets
    event = db.query(Event).filter(Event.id == booking.event_id).with_for_update().first()
    event.available_tickets += booking.ticket_quantity
    
    create_notification(
        db=db,
        user_id=user_id,
        title="Booking Cancelled",
        message=f"Your booking for {event.title} has been cancelled.",
        type=NotificationType.BOOKING
    )
    
    try:
        db.commit()
        db.refresh(booking)
        from app.services.availability_service import broadcast_current_availability
        broadcast_current_availability(db, event.id)
        return booking
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Cancellation failed due to internal error")
