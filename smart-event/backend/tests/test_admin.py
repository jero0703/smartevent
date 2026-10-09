from fastapi.testclient import TestClient

def test_admin_get_users(client: TestClient, auth_header_admin):
    res = client.get("/admin/users", headers=auth_header_admin)
    assert res.status_code == 200
    assert isinstance(res.json(), list)

def test_admin_get_overview_analytics(client: TestClient, auth_header_admin):
    res = client.get("/admin/analytics/overview", headers=auth_header_admin)
    assert res.status_code == 200
    data = res.json()
    assert "total_users" in data
    assert "total_revenue" in data
