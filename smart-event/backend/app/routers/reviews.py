from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.models.user import User
from app.schemas.review import (
    ReviewCreate,
    ReviewUpdate,
    ReviewResponse,
    EventRatingResponse
)
from app.services.auth_service import get_current_user
from app.services.review_service import (
    create_event_review,
    get_event_reviews,
    get_user_reviews,
    update_user_review,
    delete_user_review,
    get_event_rating_summary
)

router = APIRouter(tags=["Reviews"])

@router.post("/events/{event_id}/reviews", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
def submit_review(
    event_id: int,
    review_in: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    review = create_event_review(
        db=db,
        user=current_user,
        event_id=event_id,
        rating=review_in.rating,
        review_text=review_in.review_text
    )
    res = ReviewResponse.model_validate(review)
    res.username = current_user.username
    return res

@router.get("/events/{event_id}/reviews", response_model=List[ReviewResponse])
def get_reviews_for_event(
    event_id: int,
    db: Session = Depends(get_db)
):
    return get_event_reviews(db, event_id)

@router.get("/events/{event_id}/rating", response_model=EventRatingResponse)
def get_event_rating(
    event_id: int,
    db: Session = Depends(get_db)
):
    return get_event_rating_summary(db, event_id)

@router.get("/reviews/my", response_model=List[ReviewResponse])
def get_my_reviews(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return get_user_reviews(db, current_user.id)

@router.put("/reviews/{review_id}", response_model=ReviewResponse)
def update_review(
    review_id: int,
    review_in: ReviewUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    review = update_user_review(
        db=db,
        user=current_user,
        review_id=review_id,
        rating=review_in.rating,
        review_text=review_in.review_text
    )
    res = ReviewResponse.model_validate(review)
    res.username = current_user.username
    return res

@router.delete("/reviews/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_review(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    delete_user_review(db, current_user, review_id)
