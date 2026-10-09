from sqlalchemy.orm import Session
from datetime import datetime
from app.models.event import Event, EventStatus

def update_event_status(db: Session, event: Event) -> Event:
    """
    Updates the event status based on current time.
    Future event -> UPCOMING
    Current event time -> ONGOING
    Event finished (e.g. 24 hours after start) -> COMPLETED
    Cancelled events are not overwritten.
    """
    if event.event_status == EventStatus.CANCELLED:
        return event

    now = datetime.now()
    # Simple logic: ONGOING if it's within the event date day, COMPLETED if past.
    # We will assume an event lasts 12 hours for ONGOING.
    from datetime import timedelta
    
    if now < event.event_date:
        if event.event_status != EventStatus.UPCOMING:
            event.event_status = EventStatus.UPCOMING
            db.commit()
    elif now >= event.event_date and now <= event.event_date + timedelta(hours=12):
        if event.event_status != EventStatus.ONGOING:
            event.event_status = EventStatus.ONGOING
            db.commit()
    else:
        if event.event_status != EventStatus.COMPLETED:
            event.event_status = EventStatus.COMPLETED
            db.commit()
            
    return event
