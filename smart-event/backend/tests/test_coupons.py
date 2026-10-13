import pytest
import datetime
from app.models.coupon import DiscountType
from app.models.event import Event

def test_admin_create_and_deactivate_coupon(client, auth_header_admin, auth_header):
    # Non-admin cannot create
    unauth = client.post("/coupons", json={
        "coupon_code": "FAIL10",
        "discount_type": "PERCENTAGE",
        "discount_value": 10.0,
        "minimum_booking_amount": 50.0,
        "expiry_date": (datetime.datetime.now() + datetime.timedelta(days=10)).isoformat(),
        "is_active": True
    }, headers=auth_header)
    assert unauth.status_code == 403

    # Admin creates valid percentage coupon
    create_res = client.post("/coupons", json={
        "coupon_code": "DISCOUNT10",
        "discount_type": "PERCENTAGE",
        "discount_value": 10.0,
        "minimum_booking_amount": 50.0,
        "expiry_date": (datetime.datetime.now() + datetime.timedelta(days=10)).isoformat(),
        "usage_limit": 2,
        "is_active": True
    }, headers=auth_header_admin)
    assert create_res.status_code == 201
    coupon_id = create_res.json()["id"]
    assert create_res.json()["coupon_code"] == "DISCOUNT10"

    # Admin deactivates coupon
    deact_res = client.patch(f"/coupons/{coupon_id}/deactivate", headers=auth_header_admin)
    assert deact_res.status_code == 200
    assert deact_res.json()["is_active"] == False

def test_coupon_validation_rules(client, auth_header_admin):
    # Create an active percentage coupon
    client.post("/coupons", json={
        "coupon_code": "SAVE20",
        "discount_type": "PERCENTAGE",
        "discount_value": 20.0,
        "minimum_booking_amount": 100.0,
        "expiry_date": (datetime.datetime.now() + datetime.timedelta(days=5)).isoformat(),
        "usage_limit": 10,
        "is_active": True
    }, headers=auth_header_admin)

    # 1. Valid validation
    val_res = client.post("/coupons/validate", json={
        "coupon_code": "save20",
        "booking_amount": 200.0
    })
    assert val_res.status_code == 200
    assert val_res.json()["discount_amount"] == 40.0
    assert val_res.json()["final_amount"] == 160.0

    # 2. Minimum amount not met
    low_res = client.post("/coupons/validate", json={
        "coupon_code": "SAVE20",
        "booking_amount": 50.0
    })
    assert low_res.status_code == 400
    assert "at least" in low_res.json()["detail"].lower()

    # 3. Nonexistent coupon
    fake_res = client.post("/coupons/validate", json={
        "coupon_code": "NONEXISTENT",
        "booking_amount": 200.0
    })
    assert fake_res.status_code == 404

def test_expired_coupon(client, auth_header_admin):
    # Expired coupon
    client.post("/coupons", json={
        "coupon_code": "EXPIRED50",
        "discount_type": "FIXED",
        "discount_value": 50.0,
        "minimum_booking_amount": 0.0,
        "expiry_date": (datetime.datetime.now() - datetime.timedelta(days=1)).isoformat(),
        "is_active": True
    }, headers=auth_header_admin)

    res = client.post("/coupons/validate", json={
        "coupon_code": "EXPIRED50",
        "booking_amount": 100.0
    })
    assert res.status_code == 400
    assert "expired" in res.json()["detail"].lower()

def test_booking_with_coupon(client, db, auth_header, auth_header_admin):
    # Create coupon
    client.post("/coupons", json={
        "coupon_code": "FLAT15",
        "discount_type": "FIXED",
        "discount_value": 15.0,
        "minimum_booking_amount": 20.0,
        "expiry_date": (datetime.datetime.now() + datetime.timedelta(days=5)).isoformat(),
        "is_active": True
    }, headers=auth_header_admin)

    # Create event
    event = Event(
        title="Coupon Event",
        category="Tech",
        location="Hall A",
        event_date=datetime.datetime.now() + datetime.timedelta(days=5),
        ticket_price=25.0,
        total_tickets=50,
        available_tickets=50
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    # Book with coupon
    res = client.post("/bookings", json={
        "event_id": event.id,
        "ticket_quantity": 2,
        "coupon_code": "FLAT15"
    }, headers=auth_header)
    assert res.status_code == 201
    data = res.json()
    assert data["total_price"] == 50.0
    assert data["discount_amount"] == 15.0
    assert data["final_amount"] == 35.0
