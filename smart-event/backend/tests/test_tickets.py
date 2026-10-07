def test_ticket_generated_and_verification(client, db):
    # Create user and login
    client.post("/auth/register", json={"username": "tkt", "email": "tkt@example.com", "password": "pass"})
    res = client.post("/auth/login", data={"username": "tkt@example.com", "password": "pass"})
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create event
    import datetime
    from app.models.event import Event
    event = Event(title="E", category="Music", location="L", event_date=datetime.datetime.now() + datetime.timedelta(days=1), ticket_price=10.0, total_tickets=10, available_tickets=10)
    db.add(event)
    db.commit()
    db.refresh(event)
    
    # Create booking
    client.post("/bookings", json={"event_id": event.id, "ticket_quantity": 1}, headers=headers)
    
    # Get tickets
    tickets_res = client.get("/tickets/my", headers=headers)
    assert tickets_res.status_code == 200
    tickets = tickets_res.json()
    assert len(tickets) == 1
    
    ticket_code = tickets[0]["ticket_code"]
    
    # Verify ticket
    verify_res = client.get(f"/tickets/verify/{ticket_code}")
    assert verify_res.status_code == 200
    assert verify_res.json()["valid"] == True
    
    # Invalid ticket
    invalid_res = client.get("/tickets/verify/INVALID-CODE")
    assert invalid_res.status_code == 404
