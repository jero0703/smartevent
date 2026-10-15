import pytest
import datetime
from app.models.event import Event, EventCategory, EventStatus

def test_chatbot_service_and_endpoints(client, db, auth_header):
    # 1. Health check
    health_res = client.get("/chatbot/health")
    assert health_res.status_code == 200
    assert health_res.json()["status"] == "healthy"

    # 2. General FAQ queries (unauthenticated or authenticated)
    faq_res = client.post("/chatbot/chat", json={
        "message": "How do I cancel my booking and get a refund?"
    })
    assert faq_res.status_code == 200
    assert "cancel" in faq_res.json()["response"].lower()
    assert faq_res.json()["context_type"] == "faq"

    # 3. Create test event
    now = datetime.datetime.now()
    event = Event(
        title="AI Chat Conference",
        category=EventCategory.Tech,
        location="Convention Center",
        event_date=now + datetime.timedelta(days=15),
        ticket_price=75.0,
        total_tickets=50,
        available_tickets=50,
        event_status=EventStatus.UPCOMING
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    # 4. Search query via chatbot
    search_res = client.post("/chatbot/chat", json={
        "message": "Find tech events under 100"
    })
    assert search_res.status_code == 200
    assert "AI Chat Conference" in search_res.json()["response"]

    # 5. Authenticated user asks for my bookings before booking
    book_ask1 = client.post("/chatbot/chat", json={
        "message": "Show my bookings"
    }, headers=auth_header)
    assert book_ask1.status_code == 200
    assert "no bookings" in book_ask1.json()["response"].lower()

    # 6. User books tickets, then asks chatbot
    client.post("/bookings", json={"event_id": event.id, "ticket_quantity": 2}, headers=auth_header)

    book_ask2 = client.post("/chatbot/chat", json={
        "message": "Show my bookings"
    }, headers=auth_header)
    assert book_ask2.status_code == 200
    assert "AI Chat Conference" in book_ask2.json()["response"]

    # 7. Unauthenticated user asking for bookings is prompted to login
    unauth_ask = client.post("/chatbot/chat", json={
        "message": "Show my bookings"
    })
    assert unauth_ask.status_code == 200
    assert "log in" in unauth_ask.json()["response"].lower()

    # 8. Chat history retrieval & clearing
    history_res = client.get("/chatbot/history", headers=auth_header)
    assert history_res.status_code == 200
    assert len(history_res.json()) >= 2

    clear_res = client.delete("/chatbot/history", headers=auth_header)
    assert clear_res.status_code == 200

    history_empty = client.get("/chatbot/history", headers=auth_header)
    assert len(history_empty.json()) == 0
