import pytest
import datetime
from app.models.event import Event, EventCategory, EventStatus

def test_recommendations_workflow(client, db, auth_header):
    now = datetime.datetime.now()
    e_tech1 = Event(
        title="AI Hackathon",
        category=EventCategory.Tech,
        location="Coimbatore",
        event_date=now + datetime.timedelta(days=3),
        ticket_price=25.0,
        total_tickets=100,
        available_tickets=100,
        event_status=EventStatus.UPCOMING
    )
    e_tech2 = Event(
        title="Cloud Summit",
        category=EventCategory.Tech,
        location="Bangalore",
        event_date=now + datetime.timedelta(days=6),
        ticket_price=40.0,
        total_tickets=50,
        available_tickets=50,
        event_status=EventStatus.UPCOMING
    )
    e_music = Event(
        title="Jazz Night",
        category=EventCategory.Music,
        location="Chennai",
        event_date=now + datetime.timedelta(days=4),
        ticket_price=30.0,
        total_tickets=100,
        available_tickets=100,
        event_status=EventStatus.UPCOMING
    )
    db.add_all([e_tech1, e_tech2, e_music])
    db.commit()

    # 1. Record event view
    view_res = client.post(f"/events/{e_tech1.id}/view", headers=auth_header)
    assert view_res.status_code == 200

    # 2. Check similar events for e_tech1 -> should return e_tech2
    sim_res = client.get(f"/recommendations/similar/{e_tech1.id}")
    assert sim_res.status_code == 200
    sim_titles = [item["title"] for item in sim_res.json()["items"]]
    assert "Cloud Summit" in sim_titles
    assert "AI Hackathon" not in sim_titles

    # 3. Check trending events
    trend_res = client.get("/recommendations/trending")
    assert trend_res.status_code == 200
    assert len(trend_res.json()["items"]) >= 1

    # 4. Check personalized recommendations for user
    rec_res = client.get("/recommendations/for-you", headers=auth_header)
    assert rec_res.status_code == 200
    rec_items = rec_res.json()["items"]
    assert len(rec_items) >= 1
    # Tech events should be prioritized due to the view
    rec_categories = [item["category"] for item in rec_items]
    assert "Tech" in rec_categories
