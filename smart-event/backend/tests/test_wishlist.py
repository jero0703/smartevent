import pytest
import datetime
from app.models.event import Event, EventCategory, EventStatus

def test_wishlist_lifecycle(client, db, auth_header):
    now = datetime.datetime.now()
    event = Event(
        title="Wishlist Gala",
        category=EventCategory.Business,
        location="Hotel Ballroom",
        event_date=now + datetime.timedelta(days=7),
        ticket_price=100.0,
        total_tickets=50,
        available_tickets=50,
        event_status=EventStatus.UPCOMING
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    # 1. Check initial status
    status_res = client.get(f"/wishlist/{event.id}/status", headers=auth_header)
    assert status_res.status_code == 200
    assert status_res.json()["is_saved"] == False

    # 2. Add to wishlist
    add_res = client.post(f"/wishlist/{event.id}", headers=auth_header)
    assert add_res.status_code == 201
    assert add_res.json()["event_id"] == event.id

    # 3. Check status is now true
    status_res2 = client.get(f"/wishlist/{event.id}/status", headers=auth_header)
    assert status_res2.status_code == 200
    assert status_res2.json()["is_saved"] == True

    # 4. Duplicate add rejected with 409
    dup_res = client.post(f"/wishlist/{event.id}", headers=auth_header)
    assert dup_res.status_code == 409

    # 5. List wishlist items
    list_res = client.get("/wishlist", headers=auth_header)
    assert list_res.status_code == 200
    assert list_res.json()["total"] == 1
    assert list_res.json()["items"][0]["event"]["title"] == "Wishlist Gala"

    # 6. Remove from wishlist
    del_res = client.delete(f"/wishlist/{event.id}", headers=auth_header)
    assert del_res.status_code == 200

    # 7. List wishlist is now empty
    list_res2 = client.get("/wishlist", headers=auth_header)
    assert list_res2.json()["total"] == 0

    # 8. Deleting again returns 404
    del_res2 = client.delete(f"/wishlist/{event.id}", headers=auth_header)
    assert del_res2.status_code == 404

def test_wishlist_unauthorized(client):
    res = client.get("/wishlist")
    assert res.status_code == 401
