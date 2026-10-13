from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.models.notification import Notification, NotificationType
from app.models.booking import Booking, BookingStatus
from app.models.event import Event, EventStatus

def create_notification(
    db: Session,
    user_id: int,
    title: str,
    message: str,
    type: NotificationType
) -> Notification:
    """
    Creates a notification for a user with duplicate prevention.
    Populates both 'type' and 'notification_type' columns for full compatibility.
    """
    existing = db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.title == title,
        Notification.message == message
    ).first()
    if existing:
        return existing

    notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        type=type,
        notification_type=type
    )
    db.add(notification)
    db.flush()
    return notification

def generate_event_reminder(db: Session, user_id: int, event_title: str):
    """
    Single event reminder generator.
    """
    create_notification(
        db=db,
        user_id=user_id,
        title="Event Reminder",
        message=f"Reminder: {event_title} is coming up soon!",
        type=NotificationType.EVENT
    )
    db.commit()

def send_upcoming_event_reminders(db: Session) -> int:
    """
    Finds confirmed bookings for events occurring in the next 24 hours
    and idempotently dispatches event reminder notifications.
    """
    now = datetime.now()
    window = now + timedelta(hours=24)
    bookings = db.query(Booking).join(Booking.event).filter(
        Booking.booking_status == BookingStatus.CONFIRMED,
        Event.event_status != EventStatus.CANCELLED,
        Event.event_date >= now,
        Event.event_date <= window
    ).all()

    reminders_sent = 0
    for b in bookings:
        title = "Upcoming Event Reminder"
        msg = f"Reminder: Your booked event '{b.event.title}' is scheduled for {b.event.event_date.strftime('%Y-%m-%d %H:%M')}!"
        existing = db.query(Notification).filter(
            Notification.user_id == b.user_id,
            Notification.title == title,
            Notification.message == msg
        ).first()
        if not existing:
            create_notification(db, b.user_id, title, msg, NotificationType.EVENT)
            reminders_sent += 1

    if reminders_sent > 0:
        db.commit()
    return reminders_sent
