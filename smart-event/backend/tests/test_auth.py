def test_register_success(client):
    response = client.post("/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "Password123"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data

def test_register_duplicate_email(client):
    client.post("/auth/register", json={
        "username": "user1",
        "email": "test@example.com",
        "password": "Password123"
    })
    response = client.post("/auth/register", json={
        "username": "user2",
        "email": "test@example.com",
        "password": "Password123"
    })
    assert response.status_code == 409

def test_login_success(client):
    client.post("/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "Password123"
    })
    response = client.post("/auth/login", data={
        "username": "test@example.com",
        "password": "Password123"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_login_invalid(client):
    response = client.post("/auth/login", data={
        "username": "wrong@example.com",
        "password": "Password123"
    })
    assert response.status_code == 401

def test_protected_endpoint_without_token(client):
    response = client.get("/users/me")
    assert response.status_code == 401
