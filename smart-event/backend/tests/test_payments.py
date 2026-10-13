import pytest
import datetime
from app.models.event import Event
from app.models.booking import Booking, BookingStatus

@pytest.fixture
def payment_user_header(client):
    client.post("/auth/register", json={
        "username": "payer",
        "email": "payer@example.com",
        "password": "Password123"
    })
    res = client.post("/auth/login", data={
        "username": "payer@example.com",
        "password": "Password123"
    })
    return {"Authorization": f"Bearer {res.json()['access_token']}"}

@pytest.fixture
def other_user_header(client):
    client.post("/auth/register", json={
        "username": "other",
        "email": "other@example.com",
        "password": "Password123"
    })
    res = client.post("/auth/login", data={
        "username": "other@example.com",
        "password": "Password123"
    })
    return {"Authorization": f"Bearer {res.json()['access_token']}"}

@pytest.fixture
def payable_event(db):
    event = Event(
        title="Payment Concert",
        category="Music",
        location="Stadium",
        event_date=datetime.datetime.now() + datetime.timedelta(days=2),
        ticket_price=50.0,
        total_tickets=100,
        available_tickets=100
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event

def test_successful_payment_workflow(client, payment_user_header, payable_event):
    # 1. Create a booking with status PENDING
    booking_res = client.post("/bookings", json={
        "event_id": payable_event.id,
        "ticket_quantity": 2,
        "status": "PENDING"
    }, headers=payment_user_header)
    assert booking_res.status_code == 201
    booking_id = booking_res.json()["id"]
    assert booking_res.json()["booking_status"] == "PENDING"

    # 2. Initiate checkout
    checkout_res = client.post("/payments/checkout", json={
        "booking_id": booking_id,
        "payment_method": "simulation"
    }, headers=payment_user_header)
    assert checkout_res.status_code == 201
    payment_id = checkout_res.json()["id"]
    assert checkout_res.json()["payment_status"] == "PENDING"
    assert checkout_res.json()["amount"] == 100.0

    # 3. Simulate success
    sim_res = client.post(f"/payments/{payment_id}/simulate-result", json={
        "status": "SUCCESS",
        "transaction_id": "TXN-TEST-123"
    }, headers=payment_user_header)
    assert sim_res.status_code == 200
    assert sim_res.json()["payment_status"] == "SUCCESS"

    # 4. Verify booking is now CONFIRMED
    booking_check = client.get(f"/bookings/{booking_id}", headers=payment_user_header)
    assert booking_check.status_code == 200
    assert booking_check.json()["booking_status"] == "CONFIRMED"

    # 5. Verify ticket generated
    tickets_res = client.get("/tickets/my", headers=payment_user_header)
    assert tickets_res.status_code == 200
    assert len(tickets_res.json()) >= 1

    # 6. Prevent repeated successful charge on same booking
    dup_checkout = client.post("/payments/checkout", json={
        "booking_id": booking_id
    }, headers=payment_user_header)
    assert dup_checkout.status_code == 400
    assert "already been paid" in dup_checkout.json()["detail"].lower()

def test_failed_payment_workflow(client, payment_user_header, payable_event):
    booking_res = client.post("/bookings", json={
        "event_id": payable_event.id,
        "ticket_quantity": 1,
        "status": "PENDING"
    }, headers=payment_user_header)
    booking_id = booking_res.json()["id"]

    checkout_res = client.post("/payments/checkout", json={
        "booking_id": booking_id
    }, headers=payment_user_header)
    payment_id = checkout_res.json()["id"]

    # Simulate failure
    sim_res = client.post(f"/payments/{payment_id}/simulate-result", json={
        "status": "FAILED"
    }, headers=payment_user_header)
    assert sim_res.status_code == 200
    assert sim_res.json()["payment_status"] == "FAILED"

    # Booking remains PENDING
    booking_check = client.get(f"/bookings/{booking_id}", headers=payment_user_header)
    assert booking_check.json()["booking_status"] == "PENDING"

def test_payment_ownership_checks(client, payment_user_header, other_user_header, payable_event):
    booking_res = client.post("/bookings", json={
        "event_id": payable_event.id,
        "ticket_quantity": 1,
        "status": "PENDING"
    }, headers=payment_user_header)
    booking_id = booking_res.json()["id"]

    checkout_res = client.post("/payments/checkout", json={
        "booking_id": booking_id
    }, headers=payment_user_header)
    payment_id = checkout_res.json()["id"]

    # Other user cannot view payment
    forbidden_get = client.get(f"/payments/{payment_id}", headers=other_user_header)
    assert forbidden_get.status_code == 403

    # Other user cannot simulate result
    forbidden_sim = client.post(f"/payments/{payment_id}/simulate-result", json={
        "status": "SUCCESS"
    }, headers=other_user_header)
    assert forbidden_sim.status_code == 403
