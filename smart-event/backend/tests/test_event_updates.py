import pytest
import datetime
from app.models.event import Event, EventCategory, EventStatus

def test_event_updates_permissions_and_crud(client, db, auth_header, auth_header_organizer, auth_header_admin):
    # 1. Organizer creates an event
    create_event_res = client.post("/organizer/events", json={
        "title": "Announcements Festival",
        "description": "Live announcements",
        "category": "Music",
        "location": "Park",
        "event_date": (datetime.datetime.now() + datetime.timedelta(days=10)).isoformat(),
        "ticket_price": 50.0,
        "total_tickets": 100
    }, headers=auth_header_organizer)
    assert create_event_res.status_code == 201
    event_id = create_event_res.json()["id"]

    # 2. Regular user cannot post announcement (403)
    unauth_post = client.post(f"/events/{event_id}/updates", json={
        "message": "Gate opens at 4pm"
    }, headers=auth_header)
    assert unauth_post.status_code == 403

    # 3. Event Organizer posts announcement
    org_post = client.post(f"/events/{event_id}/updates", json={
        "message": "Gate opens at 4pm"
    }, headers=auth_header_organizer)
    assert org_post.status_code == 201
    update_id = org_post.json()["id"]
    assert org_post.json()["message"] == "Gate opens at 4pm"

    # 4. Public can view announcements
    get_res = client.get(f"/events/{event_id}/updates")
    assert get_res.status_code == 200
    assert len(get_res.json()) == 1
    assert get_res.json()[0]["message"] == "Gate opens at 4pm"

    # 5. Regular user cannot modify announcement
    unauth_put = client.put(f"/event-updates/{update_id}", json={
        "message": "Gate opens at 5pm"
    }, headers=auth_header)
    assert unauth_put.status_code == 403

    # 6. Admin can modify announcement
    admin_put = client.put(f"/event-updates/{update_id}", json={
        "message": "Gate opens at 5pm"
    }, headers=auth_header_admin)
    assert admin_put.status_code == 200
    assert admin_put.json()["message"] == "Gate opens at 5pm"

    # 7. Organizer deletes announcement
    org_del = client.delete(f"/event-updates/{update_id}", headers=auth_header_organizer)
    assert org_del.status_code == 204

    # 8. Get updates is now empty
    get_res2 = client.get(f"/events/{event_id}/updates")
    assert len(get_res2.json()) == 0

def test_event_updates_websocket(client, db):
    now = datetime.datetime.now()
    event = Event(
        title="WS Announcement Event",
        category=EventCategory.Sports,
        location="Stadium",
        event_date=now + datetime.timedelta(days=2),
        ticket_price=10.0,
        total_tickets=20,
        available_tickets=20,
        event_status=EventStatus.UPCOMING
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    with client.websocket_connect(f"/ws/events/{event.id}/updates") as websocket:
        initial = websocket.receive_json()
        assert initial["event_id"] == event.id
        assert initial["type"] == "connected"

        websocket.send_text("ping")
        assert websocket.receive_text() == "pong"
