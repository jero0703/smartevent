import pytest
import datetime
from app.models.event import Event, EventCategory, EventStatus

def test_event_availability_rest(client, db, auth_header):
    now = datetime.datetime.now()
    event = Event(
        title="Availability Concert",
        category=EventCategory.Music,
        location="Arena",
        event_date=now + datetime.timedelta(days=5),
        ticket_price=50.0,
        total_tickets=10,
        available_tickets=10,
        event_status=EventStatus.UPCOMING
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    # 1. Initial availability
    res = client.get(f"/events/{event.id}/availability")
    assert res.status_code == 200
    data = res.json()
    assert data["event_id"] == event.id
    assert data["total_capacity"] == 10
    assert data["tickets_sold"] == 0
    assert data["available_tickets"] == 10

    # 2. Book 4 tickets
    book_res = client.post("/bookings", json={
        "event_id": event.id,
        "ticket_quantity": 4
    }, headers=auth_header)
    assert book_res.status_code == 201
    booking_id = book_res.json()["id"]

    # 3. Check updated availability
    res2 = client.get(f"/events/{event.id}/availability")
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["tickets_sold"] == 4
    assert data2["available_tickets"] == 6

    # 4. Overbooking prevention: Requesting more than available tickets
    overbook = client.post("/bookings", json={
        "event_id": event.id,
        "ticket_quantity": 7
    }, headers=auth_header)
    assert overbook.status_code == 400
    assert "not enough tickets" in overbook.json()["detail"].lower()

    # 5. Cancel booking restores availability
    cancel_res = client.patch(f"/bookings/{booking_id}/cancel", headers=auth_header)
    assert cancel_res.status_code == 200

    res3 = client.get(f"/events/{event.id}/availability")
    assert res3.status_code == 200
    data3 = res3.json()
    assert data3["tickets_sold"] == 0
    assert data3["available_tickets"] == 10

def test_event_availability_websocket(client, db):
    now = datetime.datetime.now()
    event = Event(
        title="WS Concert",
        category=EventCategory.Music,
        location="Arena",
        event_date=now + datetime.timedelta(days=5),
        ticket_price=20.0,
        total_tickets=50,
        available_tickets=50,
        event_status=EventStatus.UPCOMING
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    with client.websocket_connect(f"/ws/events/{event.id}/availability") as websocket:
        initial = websocket.receive_json()
        assert initial["event_id"] == event.id
        assert initial["type"] == "initial_state"
        assert initial["total_capacity"] == 50
        assert initial["available_tickets"] == 50

        # Test ping-pong
        websocket.send_text("ping")
        pong = websocket.receive_text()
        assert pong == "pong"
