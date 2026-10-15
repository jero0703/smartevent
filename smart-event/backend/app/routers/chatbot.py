from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.core.config import settings
from app.models.user import User
from app.models.chat_history import ChatHistory
from app.schemas.chatbot import (
    ChatbotMessageRequest,
    ChatbotMessageResponse,
    ChatHistoryItem,
    ChatbotHealthResponse
)
from app.services.auth_service import get_current_user
from app.utils.dependencies import get_optional_user
from app.services.chatbot_service import process_chat_message, record_chat_history

router = APIRouter(prefix="/chatbot", tags=["Chatbot"])

@router.post("/chat", response_model=ChatbotMessageResponse)
def chat_with_bot(
    req: ChatbotMessageRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    result = process_chat_message(db, req.message, current_user)
    
    # Save conversation history for logged in user
    if current_user:
        record_chat_history(db, current_user.id, req.message, result["response"])

    return ChatbotMessageResponse(
        role="assistant",
        response=result["response"],
        context_type=result.get("context_type"),
        data=result.get("data")
    )

@router.get("/history", response_model=List[ChatHistoryItem])
def get_chat_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    history = db.query(ChatHistory).filter(
        ChatHistory.user_id == current_user.id
    ).order_by(ChatHistory.created_at.asc()).limit(50).all()
    return history

@router.delete("/history", status_code=status.HTTP_200_OK)
def clear_chat_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db.query(ChatHistory).filter(ChatHistory.user_id == current_user.id).delete()
    db.commit()
    return {"message": "Chat history cleared successfully"}

@router.get("/health", response_model=ChatbotHealthResponse)
def chatbot_health():
    return ChatbotHealthResponse(
        status="healthy",
        provider=settings.AI_PROVIDER,
        ai_enabled=bool(settings.AI_API_KEY)
    )
