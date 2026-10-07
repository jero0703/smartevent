import pytest
import datetime

@pytest.fixture
def auth_header(client):
    client.post("/auth/register", json={
        "username": "booker",
        "email": "booker@example.com",
        "password": "Password123"
    })
    res = client.post("/auth/login", data={
        "username": "booker@example.com",
        "password": "Password123"
    })
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def test_event(db):
    from app.models.event import Event
    event = Event(
        title="Bookable Event",
        category="Music",
        location="Test Loc",
        event_date=datetime.datetime.now() + datetime.timedelta(days=1),
        ticket_price=10.0,
        total_tickets=10,
        available_tickets=10
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event

def test_create_booking(client, auth_header, test_event):
    response = client.post("/bookings", json={
        "event_id": test_event.id,
        "ticket_quantity": 2
    }, headers=auth_header)
    assert response.status_code == 201
    assert response.json()["total_price"] == 20.0

def test_insufficient_tickets(client, auth_header, test_event):
    response = client.post("/bookings", json={
        "event_id": test_event.id,
        "ticket_quantity": 20
    }, headers=auth_header)
    assert response.status_code == 400

def test_booking_history(client, auth_header, test_event):
    client.post("/bookings", json={"event_id": test_event.id, "ticket_quantity": 1}, headers=auth_header)
    response = client.get("/bookings/my", headers=auth_header)
    assert response.status_code == 200
    assert len(response.json()["items"]) == 1

def test_cancel_booking(client, auth_header, test_event):
    res = client.post("/bookings", json={"event_id": test_event.id, "ticket_quantity": 2}, headers=auth_header)
    booking_id = res.json()["id"]
    
    response = client.patch(f"/bookings/{booking_id}/cancel", headers=auth_header)
    assert response.status_code == 200
    assert response.json()["booking_status"] == "CANCELLED"
