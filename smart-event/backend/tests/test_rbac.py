from fastapi.testclient import TestClient

def test_user_cannot_create_event(client: TestClient, auth_header):
    event_data = {
        "title": "Unauthorized Event",
        "category": "Tech",
        "location": "NY",
        "event_date": "2030-10-10T10:00:00",
        "ticket_price": 50,
        "total_tickets": 100
    }
    res = client.post("/organizer/events", json=event_data, headers=auth_header)
    assert res.status_code == 403

def test_organizer_can_create_event(client: TestClient, auth_header_organizer):
    event_data = {
        "title": "Authorized Event",
        "description": "Desc",
        "category": "Tech",
        "location": "NY",
        "event_date": "2030-10-10T10:00:00",
        "ticket_price": 50,
        "total_tickets": 100
    }
    res = client.post("/organizer/events", json=event_data, headers=auth_header_organizer)
    assert res.status_code == 201

def test_user_cannot_access_admin_endpoints(client: TestClient, auth_header):
    res = client.get("/admin/users", headers=auth_header)
    assert res.status_code == 403

def test_admin_can_access_admin_endpoints(client: TestClient, auth_header_admin):
    res = client.get("/admin/users", headers=auth_header_admin)
    assert res.status_code == 200
