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

