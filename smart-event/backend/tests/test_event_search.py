import pytest
import datetime
from app.models.event import Event, EventCategory, EventStatus
from app.models.booking import Booking, BookingStatus

def test_event_search_and_filtering(client, db):
    now = datetime.datetime.now()
    e1 = Event(
        title="AI World Summit",
        description="Artificial intelligence and robotics",
        category=EventCategory.Tech,
        location="Chennai",
        event_date=now + datetime.timedelta(days=5),
        ticket_price=150.0,
        total_tickets=100,
        available_tickets=100,
        event_status=EventStatus.UPCOMING
    )
    e2 = Event(
        title="Rock Music Night",
        description="Live rock bands",
        category=EventCategory.Music,
        location="Bangalore",
        event_date=now + datetime.timedelta(days=10),
        ticket_price=50.0,
        total_tickets=200,
        available_tickets=200,
        event_status=EventStatus.UPCOMING
    )
    e3 = Event(
        title="Cancelled Marathon",
        description="Sports event that got cancelled",
        category=EventCategory.Sports,
        location="Chennai",
        event_date=now + datetime.timedelta(days=15),
        ticket_price=20.0,
        total_tickets=50,
        available_tickets=50,
        event_status=EventStatus.CANCELLED
    )
    db.add_all([e1, e2, e3])
    db.commit()

    # 1. Cancelled event must NOT appear in public listing
    all_events = client.get("/events")
    assert all_events.status_code == 200
    titles = [item["title"] for item in all_events.json()["items"]]
    assert "Cancelled Marathon" not in titles
    assert "AI World Summit" in titles

    # 2. Search by title
    search_res = client.get("/events?search=Summit")
    assert search_res.status_code == 200
    assert len(search_res.json()["items"]) == 1
    assert search_res.json()["items"][0]["title"] == "AI World Summit"

    # 3. Filter by location & category
    loc_res = client.get("/events?location=Chennai&category=Tech")
    assert loc_res.status_code == 200
    assert len(loc_res.json()["items"]) == 1

    # 4. Filter by price range
    price_res = client.get("/events?min_price=40&max_price=100")
    assert price_res.status_code == 200
    assert len(price_res.json()["items"]) == 1
    assert price_res.json()["items"][0]["title"] == "Rock Music Night"

    # 5. Invalid price range
    inv_price = client.get("/events?min_price=100&max_price=50")
    assert inv_price.status_code == 400

    # 6. Invalid date range
    inv_date = client.get(f"/events?start_date={(now + datetime.timedelta(days=10)).isoformat()}&end_date={(now + datetime.timedelta(days=2)).isoformat()}")
    assert inv_date.status_code == 400

    # 7. Sorting by price asc / desc
    sort_price_asc = client.get("/events?sort_by=price&sort_order=asc")
    assert sort_price_asc.status_code == 200
    prices = [item["ticket_price"] for item in sort_price_asc.json()["items"]]
    assert prices == sorted(prices)
