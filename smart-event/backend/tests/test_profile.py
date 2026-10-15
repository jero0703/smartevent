import pytest
import datetime
from app.models.event import Event, EventCategory, EventStatus

def test_user_profile_and_booking_summary(client, db, auth_header):
    # 1. Get profile
    profile_res = client.get("/users/me", headers=auth_header)
    assert profile_res.status_code == 200
    user_data = profile_res.json()
    assert "email" in user_data
    assert "role" in user_data
    assert "hashed_password" not in user_data

    # 2. Update profile fields
    patch_res = client.patch("/users/me", json={
        "phone_number": "+1234567890",
        "location": "Chennai",
        "full_name": "Test User",
        "bio": "Event lover"
    }, headers=auth_header)
    assert patch_res.status_code == 200
    updated = patch_res.json()
    assert updated["phone_number"] == "+1234567890"
    assert updated["location"] == "Chennai"
    assert updated["full_name"] == "Test User"

    # 3. Security: Attempting to change role should be ignored / forbidden
    hack_res = client.patch("/users/me", json={
        "role": "ADMIN"
    }, headers=auth_header)
    assert hack_res.status_code == 200
    assert hack_res.json()["role"] == "USER"

    # 4. Create an event and a booking to test booking summary
    now = datetime.datetime.now()
    event = Event(
        title="Summary Festival",
        category=EventCategory.Music,
        location="Chennai",
        event_date=now + datetime.timedelta(days=5),
        ticket_price=40.0,
        total_tickets=100,
        available_tickets=100,
        event_status=EventStatus.UPCOMING
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    client.post("/bookings", json={
        "event_id": event.id,
        "ticket_quantity": 2
    }, headers=auth_header)

    summary_res = client.get("/users/me/booking-summary", headers=auth_header)
    assert summary_res.status_code == 200
    summary = summary_res.json()
    assert summary["total_bookings"] == 1
    assert summary["confirmed_bookings"] == 1
    assert summary["total_tickets_booked"] == 2
    assert summary["total_spent"] == 80.0
    assert len(summary["upcoming_events"]) == 1

    # 5. Activity summary
    # View the event first
    client.post(f"/events/{event.id}/view", headers=auth_header)
    # Wishlist the event
    client.post(f"/wishlist/{event.id}", headers=auth_header)

    act_res = client.get("/users/me/activity", headers=auth_header)
    assert act_res.status_code == 200
    act = act_res.json()
    assert len(act["recent_views"]) >= 1
    assert act["wishlist_count"] == 1
