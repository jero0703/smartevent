from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from app.core.database import get_db
from app.models.user import User
from app.models.event import EventCategory
from app.schemas.event import PaginatedEventResponse
from app.services.auth_service import get_current_user
from app.services.recommendation_service import (
    get_personalized_recommendations_service,
    get_trending_events_service,
    get_similar_events_service
)

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])

@router.get("/for-you", response_model=PaginatedEventResponse)
def get_personalized_recommendations(
    category: Optional[EventCategory] = None,
    location: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if start_date and end_date and start_date > end_date:
        raise HTTPException(status_code=400, detail="start_date cannot be greater than end_date")
    return get_personalized_recommendations_service(
        db=db,
        user=current_user,
        category=category,
        location=location,
        start_date=start_date,
        end_date=end_date,
        page=page,
        limit=limit
    )

@router.get("/trending", response_model=PaginatedEventResponse)
def get_trending_events(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    return get_trending_events_service(db=db, page=page, limit=limit)

@router.get("/similar/{event_id}", response_model=PaginatedEventResponse)
def get_similar_events(
    event_id: int,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    return get_similar_events_service(db=db, event_id=event_id, page=page, limit=limit)
