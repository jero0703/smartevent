import pytest

def test_role_based_authorizations(client, auth_header, auth_header_organizer, auth_header_admin):
    # 1. Regular user cannot access Admin endpoints
    u_admin = client.get("/admin/users", headers=auth_header)
    assert u_admin.status_code == 403

    # 2. Organizer cannot access Admin endpoints
    org_admin = client.get("/admin/users", headers=auth_header_organizer)
    assert org_admin.status_code == 403

    # 3. Regular user cannot access Organizer event creation
    u_org = client.post("/organizer/events", json={
        "title": "Hack",
        "category": "Tech",
        "location": "Loc",
        "event_date": "2030-01-01T10:00:00",
        "ticket_price": 10,
        "total_tickets": 10
    }, headers=auth_header)
    assert u_org.status_code == 403

    # 4. Regular user cannot manage coupons
    u_coupon = client.post("/coupons", json={
        "coupon_code": "USERCOUPON",
        "discount_type": "PERCENTAGE",
        "discount_value": 10,
        "minimum_booking_amount": 0,
        "expiry_date": "2030-01-01T10:00:00"
    }, headers=auth_header)
    assert u_coupon.status_code == 403

    # 5. Admin can access Admin endpoints
    adm_res = client.get("/admin/users", headers=auth_header_admin)
    assert adm_res.status_code == 200
