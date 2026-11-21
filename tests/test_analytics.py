import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def get_test_settings(tmp_path) -> Settings:
    return Settings(
        node_env="test",
        database_path=str(tmp_path / "test.sqlite"),
        admin_password="test-password-12345",
        session_secret="super-secret-key-that-is-at-least-32-chars-long",
    )


def test_analytics_requires_auth(tmp_path):
    app = create_app(get_test_settings(tmp_path))
    client = TestClient(app)
    response = client.get("/v1/analytics/trinkow")
    assert response.status_code == 401


def test_analytics_returns_overview_for_authenticated_admin(tmp_path):
    app = create_app(get_test_settings(tmp_path))
    client = TestClient(app)

    # Login first
    login_resp = client.post(
        "/v1/auth/login",
        json={"email": "admin@triworkster.com", "password": "test-password-12345"},
    )
    assert login_resp.status_code == 200

    # Request analytics
    response = client.get("/v1/analytics/trinkow?time_range=7d")
    assert response.status_code == 200
    data = response.json()
    assert "screens" in data
    assert "paywall" in data
    assert "recentEvents" in data
    assert "config" in data
    assert len(data["screens"]) > 0
    assert len(data["paywall"]["steps"]) == 4


def test_trinkow_users_requires_auth(tmp_path):
    app = create_app(get_test_settings(tmp_path))
    client = TestClient(app)
    response = client.get("/v1/analytics/trinkow/users")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_trinkow_users_list_and_password_auth(tmp_path):
    settings = get_test_settings(tmp_path)
    app = create_app(settings)
    client = TestClient(app)

    # Login
    login_resp = client.post(
        "/v1/auth/login",
        json={"email": "admin@triworkster.com", "password": "test-password-12345"},
    )
    assert login_resp.status_code == 200

    # Mock trinkow_admin_service methods
    fake_list = {
        "items": [
            {
                "id": "user-123",
                "email": "tester@example.com",
                "provider": "eposta",
                "created_at": "2026-11-21T10:00:00Z",
                "is_today": True,
                "suspended": False,
                "premium": {
                    "active": True,
                    "lifetime": False,
                    "expires_at": "2026-12-01T00:00:00Z",
                    "product": "trinkow_premium",
                    "store": "play_store",
                    "environment": "PRODUCTION",
                },
            }
        ],
        "total_users": 1,
        "today_users": 1,
        "premium_users": 1,
        "suspended_users": 0,
        "page": 1,
        "limit": 20,
        "total_pages": 1,
    }

    async def mock_list_users(*args, **kwargs):
        return fake_list

    async def mock_update_status(user_id, askida):
        return {"id": user_id, "suspended": askida}

    async def mock_delete_user(user_id, admin_password):
        from app.modules.analytics.trinkow_admin_service import TrinkowAdminAuthError
        import secrets

        if not secrets.compare_digest(admin_password, settings.admin_password):
            raise TrinkowAdminAuthError("Geçersiz yönetici şifresi.")
        return {"message": "Kullanıcı silindi."}

    app.state.trinkow_admin_service.list_users = mock_list_users
    app.state.trinkow_admin_service.update_user_status = mock_update_status
    app.state.trinkow_admin_service.delete_user = mock_delete_user

    # List users
    resp = client.get("/v1/analytics/trinkow/users")
    assert resp.status_code == 200
    res_data = resp.json()
    assert res_data["total_users"] == 1
    assert res_data["items"][0]["email"] == "tester@example.com"
    assert res_data["items"][0]["is_today"] is True
    assert res_data["items"][0]["premium"]["active"] is True

    # Update status (suspend)
    patch_resp = client.patch(
        "/v1/analytics/trinkow/users/user-123/status",
        json={"askida": True},
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["suspended"] is True

    # Delete with wrong password -> 401
    del_fail = client.request(
        "DELETE",
        "/v1/analytics/trinkow/users/user-123",
        json={"adminPassword": "wrong-password-999"},
    )
    assert del_fail.status_code == 401
    assert "Geçersiz yönetici şifresi" in del_fail.json()["message"]

    # Delete with correct password -> 200
    del_ok = client.request(
        "DELETE",
        "/v1/analytics/trinkow/users/user-123",
        json={"adminPassword": "test-password-12345"},
    )
    assert del_ok.status_code == 200
    assert "Kullanıcı silindi" in del_ok.json()["message"]


