from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
from app.schemas.event import EventResponse

class WishlistItemResponse(BaseModel):
    id: int
    user_id: int
    event_id: int
    created_at: datetime
    event: EventResponse

    model_config = {"from_attributes": True}

class PaginatedWishlistResponse(BaseModel):
    items: List[WishlistItemResponse]
    page: int
    limit: int
    total: int
    pages: int
    total_pages: Optional[int] = None

class WishlistStatusResponse(BaseModel):
    event_id: int
    is_saved: bool
