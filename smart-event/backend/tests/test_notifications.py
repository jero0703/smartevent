import datetime
from app.models.event import Event

def test_notifications(client, db):
    client.post("/auth/register", json={"username": "notif", "email": "notif@example.com", "password": "pass"})
    res = client.post("/auth/login", data={"username": "notif@example.com", "password": "pass"})
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    event = Event(title="E", category="Music", location="L", event_date=datetime.datetime.now() + datetime.timedelta(days=1), ticket_price=10.0, total_tickets=10, available_tickets=10)
    db.add(event)
    db.commit()
    db.refresh(event)
    
    client.post("/bookings", json={"event_id": event.id, "ticket_quantity": 1}, headers=headers)
    
    # Check paginated notifications
    notifs_res = client.get("/notifications", headers=headers)
    assert notifs_res.status_code == 200
    assert len(notifs_res.json()["items"]) == 1
    
    notif_id = notifs_res.json()["items"][0]["id"]

    # Check unread notifications endpoint
    unread_res = client.get("/notifications/unread", headers=headers)
    assert unread_res.status_code == 200
    assert len(unread_res.json()) >= 1
    
    # Mark single as read
    read_res = client.patch(f"/notifications/{notif_id}/read", headers=headers)
    assert read_res.status_code == 200
    assert read_res.json()["is_read"] == True

    # Mark all as read
    all_read = client.patch("/notifications/read-all", headers=headers)
    assert all_read.status_code == 200
