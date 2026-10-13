from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status
from datetime import datetime
from typing import Optional, List, Dict
from app.models.review import Review
from app.models.event import Event, EventStatus
from app.models.booking import Booking, BookingStatus
from app.models.user import User, UserRole

def create_event_review(
    db: Session,
    user: User,
    event_id: int,
    rating: int,
    review_text: Optional[str] = None
) -> Review:
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )

    # Verify user has a confirmed booking for this event
    has_booking = db.query(Booking).filter(
        Booking.user_id == user.id,
        Booking.event_id == event_id,
        Booking.booking_status == BookingStatus.CONFIRMED
    ).first()
    if not has_booking and user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only review events you have booked and confirmed"
        )

    # Permit reviews only after the event has completed
    now = datetime.now()
    if event.event_status != EventStatus.COMPLETED and event.event_date > now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reviews can only be submitted after the event has completed"
        )

    if rating < 1 or rating > 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rating must be between 1 and 5"
        )

    # Check for existing review
    existing = db.query(Review).filter(
        Review.user_id == user.id,
        Review.event_id == event_id
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already reviewed this event. Use PUT to update your review"
        )

    review = Review(
        user_id=user.id,
        event_id=event_id,
        rating=rating,
        review_text=review_text
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return review

def get_event_reviews(db: Session, event_id: int) -> List[dict]:
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )

    reviews = db.query(Review).filter(Review.event_id == event_id).all()
    results = []
    for r in reviews:
        results.append({
            "id": r.id,
            "user_id": r.user_id,
            "event_id": r.event_id,
            "username": r.user.username if r.user else "Anonymous",
            "rating": r.rating,
            "review_text": r.review_text,
            "created_at": r.created_at,
            "updated_at": r.updated_at
        })
    return results

def get_user_reviews(db: Session, user_id: int) -> List[dict]:
    reviews = db.query(Review).filter(Review.user_id == user_id).all()
    results = []
    for r in reviews:
        results.append({
            "id": r.id,
            "user_id": r.user_id,
            "event_id": r.event_id,
            "username": r.user.username if r.user else "Anonymous",
            "rating": r.rating,
            "review_text": r.review_text,
            "created_at": r.created_at,
            "updated_at": r.updated_at
        })
    return results

def update_user_review(
    db: Session,
    user: User,
    review_id: int,
    rating: Optional[int] = None,
    review_text: Optional[str] = None
) -> Review:
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )

    if review.user_id != user.id and user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to edit this review"
        )

    if rating is not None:
        if rating < 1 or rating > 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Rating must be between 1 and 5"
            )
        review.rating = rating

    if review_text is not None:
        review.review_text = review_text

    db.commit()
    db.refresh(review)
    return review

def delete_user_review(db: Session, user: User, review_id: int):
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )

    if review.user_id != user.id and user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this review"
        )

    db.delete(review)
    db.commit()

def get_event_rating_summary(db: Session, event_id: int) -> Dict[str, any]:
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )

    avg_rating, total_reviews = db.query(
        func.avg(Review.rating),
        func.count(Review.id)
    ).filter(Review.event_id == event_id).first()

    return {
        "event_id": event_id,
        "average_rating": round(float(avg_rating), 2) if avg_rating is not None else 0.0,
        "total_reviews": int(total_reviews or 0)
    }
