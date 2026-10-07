import datetime

def test_get_events(client, db):
    # Create event
    from app.models.event import Event
    event = Event(
        title="Test Event",
        category="Music",
        location="Test Loc",
        event_date=datetime.datetime.now() + datetime.timedelta(days=1),
        ticket_price=10.0,
        total_tickets=100,
        available_tickets=100
    )
    db.add(event)
    db.commit()

    response = client.get("/events")
    assert response.status_code == 200
    assert len(response.json()["items"]) == 1

def test_get_single_event(client, db):
    from app.models.event import Event
    event = Event(
        title="Test Event",
        category="Music",
        location="Test Loc",
        event_date=datetime.datetime.now() + datetime.timedelta(days=1),
        ticket_price=10.0,
        total_tickets=100,
        available_tickets=100
    )
    db.add(event)
    db.commit()

    response = client.get(f"/events/{event.id}")
    assert response.status_code == 200
    assert response.json()["title"] == "Test Event"

def test_search_events(client, db):
    from app.models.event import Event
    event = Event(
        title="Unique Concert",
        category="Music",
        location="Test Loc",
        event_date=datetime.datetime.now() + datetime.timedelta(days=1),
        ticket_price=10.0,
        total_tickets=100,
        available_tickets=100
    )
    db.add(event)
    db.commit()

    response = client.get("/events?search=unique")
    assert response.status_code == 200
    assert len(response.json()["items"]) == 1
