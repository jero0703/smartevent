from sqlalchemy.orm import Session
from app.models.notification import Notification, NotificationType

def create_notification(db: Session, user_id: int, title: str, message: str, type: NotificationType) -> Notification:
    notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        type=type
    )
    db.add(notification)
    # We do NOT commit here, we rely on the parent transaction
    db.flush() 
    return notification

def generate_event_reminder(db: Session, user_id: int, event_title: str):
    """
    This function could be called by APScheduler, Celery, etc.
    """
    create_notification(
        db=db,
        user_id=user_id,
        title="Event Reminder",
        message=f"Reminder: {event_title} is coming up soon!",
        type=NotificationType.EVENT
    )
    db.commit()
