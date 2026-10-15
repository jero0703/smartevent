from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.user import User, UserRole
from app.models.event import Event
from app.models.event_update import EventUpdate
from app.schemas.event_update import (
    EventUpdateCreate,
    EventUpdateModify,
    EventUpdateResponse
)
from app.services.auth_service import get_current_user
from app.utils.websocket_manager import notify_event_update_sync

router = APIRouter(tags=["Event Updates"])

@router.post("/events/{event_id}/updates", response_model=EventUpdateResponse, status_code=status.HTTP_201_CREATED)
def create_event_update(
    event_id: int,
    update_in: EventUpdateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )

    # Check permission: Must be the organizer who owns this event OR an admin
    if current_user.role != UserRole.ADMIN and event.organizer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the event organizer or an admin can post announcements"
        )

    announcement = EventUpdate(
        event_id=event_id,
        message=update_in.message,
        created_by=current_user.id
    )
    db.add(announcement)
    db.commit()
    db.refresh(announcement)

    # Broadcast to WebSocket subscribers after successful commit
    notify_event_update_sync(event_id, {
        "id": announcement.id,
        "event_id": announcement.event_id,
        "message": announcement.message,
        "created_by": announcement.created_by,
        "created_at": announcement.created_at.isoformat() if announcement.created_at else None,
        "type": "event_update"
    })

    return announcement

@router.get("/events/{event_id}/updates", response_model=List[EventUpdateResponse])
def get_event_updates(
    event_id: int,
    db: Session = Depends(get_db)
):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )

    updates = db.query(EventUpdate).filter(
        EventUpdate.event_id == event_id
    ).order_by(EventUpdate.created_at.desc()).all()
    return updates

@router.get("/event-updates/{update_id}", response_model=EventUpdateResponse)
def get_event_update_by_id(
    update_id: int,
    db: Session = Depends(get_db)
):
    announcement = db.query(EventUpdate).filter(EventUpdate.id == update_id).first()
    if not announcement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event announcement not found"
        )
    return announcement

@router.put("/event-updates/{update_id}", response_model=EventUpdateResponse)
def modify_event_update(
    update_id: int,
    update_in: EventUpdateModify,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    announcement = db.query(EventUpdate).filter(EventUpdate.id == update_id).first()
    if not announcement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event announcement not found"
        )

    # Check permission: Must be the organizer who owns this event OR an admin
    if current_user.role != UserRole.ADMIN and announcement.event.organizer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the event organizer or an admin can edit announcements"
        )

    announcement.message = update_in.message
    db.commit()
    db.refresh(announcement)
    return announcement

@router.delete("/event-updates/{update_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event_update(
    update_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    announcement = db.query(EventUpdate).filter(EventUpdate.id == update_id).first()
    if not announcement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event announcement not found"
        )

    if current_user.role != UserRole.ADMIN and announcement.event.organizer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the event organizer or an admin can delete announcements"
        )

    db.delete(announcement)
    db.commit()
