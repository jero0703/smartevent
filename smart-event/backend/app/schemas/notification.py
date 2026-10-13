from pydantic import BaseModel
from datetime import datetime
from app.models.notification import NotificationType

from typing import Optional

class NotificationBase(BaseModel):
    title: str
    message: str
    type: NotificationType
    notification_type: Optional[NotificationType] = None
    is_read: bool = False

class NotificationResponse(NotificationBase):
    id: int
    user_id: int
    created_at: datetime

    model_config = {"from_attributes": True}

class PaginatedNotificationResponse(BaseModel):
    items: list[NotificationResponse]
    page: int
    limit: int
    total: int
    pages: int

class UnreadCountResponse(BaseModel):
    count: int
