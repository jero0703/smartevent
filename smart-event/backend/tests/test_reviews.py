import pytest
import datetime
from app.models.event import Event, EventStatus
from app.models.booking import Booking, BookingStatus

@pytest.fixture
def attendee_header(client):
    client.post("/auth/register", json={
        "username": "reviewer",
        "email": "reviewer@example.com",
        "password": "Password123"
    })
    res = client.post("/auth/login", data={
        "username": "reviewer@example.com",
        "password": "Password123"
    })
    return {"Authorization": f"Bearer {res.json()['access_token']}"}

@pytest.fixture
def non_attendee_header(client):
    client.post("/auth/register", json={
        "username": "stranger",
        "email": "stranger@example.com",
        "password": "Password123"
    })
    res = client.post("/auth/login", data={
        "username": "stranger@example.com",
        "password": "Password123"
    })
    return {"Authorization": f"Bearer {res.json()['access_token']}"}

def test_review_workflow(client, db, attendee_header, non_attendee_header):
    # Create event as upcoming so booking succeeds
    past_event = Event(
        title="Completed Seminar",
        category="Tech",
        location="Auditorium",
        event_date=datetime.datetime.now() + datetime.timedelta(days=1),
        ticket_price=10.0,
        total_tickets=50,
        available_tickets=50,
        event_status=EventStatus.UPCOMING
    )
    db.add(past_event)
    db.commit()
    db.refresh(past_event)

    # 1. Book event for attendee while UPCOMING
    book_res = client.post("/bookings", json={
        "event_id": past_event.id,
        "ticket_quantity": 1
    }, headers=attendee_header)
    assert book_res.status_code == 201

    # 2. Mark event as finished / completed
    past_event.event_status = EventStatus.COMPLETED
    past_event.event_date = datetime.datetime.now() - datetime.timedelta(days=1)
    db.commit()

    # 3. Non-attendee cannot review
    unauth_rev = client.post(f"/events/{past_event.id}/reviews", json={
        "rating": 5,
        "review_text": "Did not attend"
    }, headers=non_attendee_header)
    assert unauth_rev.status_code == 403

    # 3. Invalid rating (<1 or >5)
    invalid_rating = client.post(f"/events/{past_event.id}/reviews", json={
        "rating": 6,
        "review_text": "Too high"
    }, headers=attendee_header)
    assert invalid_rating.status_code == 422 or invalid_rating.status_code == 400

    # 4. Valid review submission
    valid_rev = client.post(f"/events/{past_event.id}/reviews", json={
        "rating": 4,
        "review_text": "Great event!"
    }, headers=attendee_header)
    assert valid_rev.status_code == 201
    review_id = valid_rev.json()["id"]
    assert valid_rev.json()["rating"] == 4

    # 5. Duplicate review rejected
    dup_rev = client.post(f"/events/{past_event.id}/reviews", json={
        "rating": 5,
        "review_text": "Second try"
    }, headers=attendee_header)
    assert dup_rev.status_code == 409

    # 6. Check rating summary
    rating_summary = client.get(f"/events/{past_event.id}/rating")
    assert rating_summary.status_code == 200
    assert rating_summary.json()["average_rating"] == 4.0
    assert rating_summary.json()["total_reviews"] == 1

    # 7. Update own review
    update_res = client.put(f"/reviews/{review_id}", json={
        "rating": 5,
        "review_text": "Actually it was outstanding!"
    }, headers=attendee_header)
    assert update_res.status_code == 200
    assert update_res.json()["rating"] == 5

    # 8. Non-attendee cannot update/delete
    forbidden_del = client.delete(f"/reviews/{review_id}", headers=non_attendee_header)
    assert forbidden_del.status_code == 403

    # 9. Delete own review
    del_res = client.delete(f"/reviews/{review_id}", headers=attendee_header)
    assert del_res.status_code == 204

def test_future_event_review_rejected(client, db, attendee_header):
    future_event = Event(
        title="Future Gala",
        category="Music",
        location="Opera House",
        event_date=datetime.datetime.now() + datetime.timedelta(days=10),
        ticket_price=100.0,
        total_tickets=50,
        available_tickets=50,
        event_status=EventStatus.UPCOMING
    )
    db.add(future_event)
    db.commit()
    db.refresh(future_event)

    # Book event
    client.post("/bookings", json={
        "event_id": future_event.id,
        "ticket_quantity": 1
    }, headers=attendee_header)

    # Attempt to review before completion
    rev_res = client.post(f"/events/{future_event.id}/reviews", json={
        "rating": 5,
        "review_text": "Haven't attended yet"
    }, headers=attendee_header)
    assert rev_res.status_code == 400
    assert "completed" in rev_res.json()["detail"].lower()
