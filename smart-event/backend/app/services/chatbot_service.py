from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, Dict, Any
import re
import logging
from app.models.user import User
from app.models.event import Event, EventCategory, EventStatus
from app.models.booking import Booking, BookingStatus
from app.models.chat_history import ChatHistory
from app.core.config import settings

logger = logging.getLogger(__name__)

FAQ_KNOWLEDGE = {
    "booking": "To book tickets, select an upcoming event, choose your ticket quantity, apply any promo code, and submit a booking via POST /bookings. Then complete checkout via POST /payments/checkout.",
    "cancellation": "You can cancel any CONFIRMED booking for upcoming events before the event date via PATCH /bookings/{booking_id}/cancel. Once cancelled, your tickets are released back to availability.",
    "qr_ticket": "After your booking is confirmed, a unique ticket code and QR code are automatically generated. You can view all your active tickets anytime via GET /tickets/my.",
    "payment": "We support secure card payments via Stripe and an instant payment simulator for testing via POST /payments/{payment_id}/simulate-result.",
    "coupons": "You can apply promotional coupons during booking by providing a valid coupon_code. Discounts can be percentage-based or fixed amounts."
}

def process_chat_message(
    db: Session,
    message: str,
    user: Optional[User] = None
) -> Dict[str, Any]:
    clean_msg = message.strip()
    lower_msg = clean_msg.lower()

    # 1. FAQs (Cancellation, Booking process, QR tickets, Payment, Coupons)
    if any(k in lower_msg for k in ["cancel", "refund", "cancellation"]):
        return {"response": FAQ_KNOWLEDGE["cancellation"], "context_type": "faq"}
    if any(k in lower_msg for k in ["how to book", "how do i book", "buy ticket"]):
        return {"response": FAQ_KNOWLEDGE["booking"], "context_type": "faq"}
    if any(k in lower_msg for k in ["qr", "scan", "ticket code"]):
        return {"response": FAQ_KNOWLEDGE["qr_ticket"], "context_type": "faq"}
    if any(k in lower_msg for k in ["how to pay", "payment method", "stripe", "simulate payment"]):
        return {"response": FAQ_KNOWLEDGE["payment"], "context_type": "faq"}
    if any(k in lower_msg for k in ["coupon", "discount", "promo code"]):
        return {"response": FAQ_KNOWLEDGE["coupons"], "context_type": "faq"}

    # 2. User Specific Booking & Account Queries
    if any(k in lower_msg for k in ["my booking", "my ticket", "my reservation", "booked events", "show my bookings", "what are my bookings"]):
        if not user:
            response_text = "To view your bookings and tickets, please log in to your account."
            return {"response": response_text, "context_type": "auth_required", "data": None}

        user_bookings = db.query(Booking).filter(
            Booking.user_id == user.id
        ).order_by(Booking.created_at.desc()).limit(5).all()

        if not user_bookings:
            response_text = f"Hello {user.username}, you currently have no bookings on record."
            return {"response": response_text, "context_type": "bookings", "data": []}

        summary_lines = []
        for b in user_bookings:
            event_title = b.event.title if b.event else "Unknown Event"
            event_date = b.event.event_date.strftime("%Y-%m-%d %H:%M") if b.event else "N/A"
            summary_lines.append(f"- Booking #{b.id}: {event_title} ({b.ticket_quantity} tickets, Status: {b.booking_status.value}, Date: {event_date})")

        response_text = f"Here are your recent bookings, {user.username}:\n" + "\n".join(summary_lines)
        return {"response": response_text, "context_type": "bookings", "data": [b.id for b in user_bookings]}

    # 2. Trending Events Query
    if any(k in lower_msg for k in ["trending", "popular", "top event"]):
        now = datetime.now()
        trending = db.query(Event).filter(
            Event.event_status != EventStatus.CANCELLED,
            Event.event_status != EventStatus.COMPLETED,
            Event.event_date >= now
        ).limit(5).all()

        if not trending:
            response_text = "There are currently no trending upcoming events."
            return {"response": response_text, "context_type": "trending", "data": []}

        lines = [f"- {e.title} ({e.category.value}) in {e.location} on {e.event_date.strftime('%b %d, %Y')} - ${float(e.ticket_price):.2f}" for e in trending]
        response_text = "Here are the top trending events:\n" + "\n".join(lines)
        return {"response": response_text, "context_type": "trending", "data": [e.id for e in trending]}

    # 3. Recommendations Query
    if any(k in lower_msg for k in ["recommend", "for me", "what should i attend"]):
        from app.services.recommendation_service import get_personalized_recommendations_service, get_trending_events_service
        if user:
            rec_data = get_personalized_recommendations_service(db, user, limit=5)
        else:
            rec_data = get_trending_events_service(db, limit=5)

        items = rec_data.get("items", [])
        if not items:
            response_text = "I couldn't find any upcoming event recommendations at this moment."
            return {"response": response_text, "context_type": "recommendations", "data": []}

        lines = [f"- {e.title} ({e.category.value}) in {e.location} on {e.event_date.strftime('%b %d, %Y')} - ${float(e.ticket_price):.2f}" for e in items]
        greeting = f"Here are personalized recommendations for you, {user.username}:" if user else "Here are recommended events you might like:"
        response_text = greeting + "\n" + "\n".join(lines)
        return {"response": response_text, "context_type": "recommendations", "data": [e.id for e in items]}

    # 4. Search by Category or Keywords
    detected_category = None
    for cat in EventCategory:
        if cat.value.lower() in lower_msg:
            detected_category = cat
            break

    if detected_category or any(w in lower_msg for w in ["find", "search", "show me", "event", "concert", "conference"]):
        now = datetime.now()
        query = db.query(Event).filter(
            Event.event_status != EventStatus.CANCELLED,
            Event.event_status != EventStatus.COMPLETED,
            Event.event_date >= now
        )
        if detected_category:
            query = query.filter(Event.category == detected_category)

        # Price extraction (e.g., "under 50", "below 100")
        price_match = re.search(r'(?:under|below|less than|\$)\s*(\d+)', lower_msg)
        if price_match:
            max_price = float(price_match.group(1))
            query = query.filter(Event.ticket_price <= max_price)

        matches = query.limit(5).all()
        if matches:
            lines = [f"- {e.title} ({e.category.value}) in {e.location} on {e.event_date.strftime('%b %d, %Y')} - ${float(e.ticket_price):.2f}" for e in matches]
            response_text = f"I found {len(matches)} matching events for you:\n" + "\n".join(lines)
            return {"response": response_text, "context_type": "search_results", "data": [e.id for e in matches]}

    # Default Smart Assistant Response
    response_text = (
        "Hello! I am your SmartEvent AI assistant. I can help you discover upcoming events, "
        "find personalized recommendations, check ticket availability, look up your bookings, "
        "and answer questions about booking, payments, or cancellations. How may I help you today?"
    )
    return {"response": response_text, "context_type": "general"}

def record_chat_history(
    db: Session,
    user_id: Optional[int],
    user_msg: str,
    bot_msg: str
):
    if user_id:
        db.add(ChatHistory(user_id=user_id, role="user", message=user_msg))
        db.add(ChatHistory(user_id=user_id, role="assistant", message=bot_msg))
        db.commit()
