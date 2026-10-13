from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ReviewCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    review_text: Optional[str] = None

class ReviewUpdate(BaseModel):
    rating: Optional[int] = Field(default=None, ge=1, le=5)
    review_text: Optional[str] = None

class ReviewResponse(BaseModel):
    id: int
    user_id: int
    event_id: int
    username: Optional[str] = None
    rating: int
    review_text: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

class EventRatingResponse(BaseModel):
    event_id: int
    average_rating: float
    total_reviews: int
