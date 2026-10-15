from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class EventUpdateCreate(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)

class EventUpdateModify(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)

class EventUpdateResponse(BaseModel):
    id: int
    event_id: int
    message: str
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
