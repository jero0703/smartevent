from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Any

class ChatbotMessageRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)

class ChatbotMessageResponse(BaseModel):
    role: str = "assistant"
    response: str
    context_type: Optional[str] = None
    data: Optional[Any] = None

class ChatHistoryItem(BaseModel):
    id: int
    role: str
    message: str
    created_at: datetime

    model_config = {"from_attributes": True}

class ChatbotHealthResponse(BaseModel):
    status: str
    provider: str
    ai_enabled: bool
