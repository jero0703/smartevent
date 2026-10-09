from fastapi.testclient import TestClient

def test_organizer_create_event(client: TestClient, auth_header_organizer):
    event_data = {
        "title": "Org Event",
        "description": "Desc",
        "category": "Tech",
        "location": "NY",
        "event_date": "2030-10-10T10:00:00",
        "ticket_price": 50,
        "total_tickets": 100
    }
    res = client.post("/organizer/events", json=event_data, headers=auth_header_organizer)
    assert res.status_code == 201
    assert res.json()["title"] == "Org Event"

def test_organizer_get_analytics(client: TestClient, auth_header_organizer):
    res = client.get("/organizer/analytics", headers=auth_header_organizer)
    assert res.status_code == 200
    data = res.json()
    assert "total_events" in data
    assert "total_revenue" in data
