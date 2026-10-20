from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

import main as entrypoint
from app.config import Settings
from app.main import create_app


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    settings = Settings(
        node_env="test",
        database_path=str(tmp_path / "manager.sqlite"),
        admin_email="admin@example.com",
        admin_password="correct-password",
        session_secret="a" * 32,
        web_origin="http://localhost:5173",
        asobeast_base_url="http://localhost:3001/api/backend",
        asobeast_api_token="",
    )
    with TestClient(create_app(settings)) as test_client:
        yield test_client


def test_protects_application_data(client: TestClient) -> None:
    response = client.get("/v1/apps")
    assert response.status_code == 401


def test_logs_in_and_returns_seeded_apps(client: TestClient) -> None:
    login = client.post(
        "/v1/auth/login",
        json={"email": "admin@example.com", "password": "correct-password"},
    )
    assert login.status_code == 200
    apps = client.get("/v1/apps")
    assert apps.status_code == 200
    assert len(apps.json()) == 2


def test_returns_400_for_malformed_json(client: TestClient) -> None:
    response = client.post(
        "/v1/auth/login",
        content="{invalid",
        headers={"content-type": "application/json"},
    )
    assert response.status_code == 400


def test_allows_browser_preflight_requests(client: TestClient) -> None:
    response = client.options(
        "/v1/apps/58c51b01-41f6-413b-8947-5cbf7d816f60",
        headers={
            "origin": "http://localhost:5173",
            "access-control-request-method": "PATCH",
            "access-control-request-headers": "content-type",
        },
    )
    assert response.status_code == 200
    assert "PATCH" in response.headers["access-control-allow-methods"]
    assert "content-type" in response.headers["access-control-allow-headers"].lower()
    assert response.headers["access-control-allow-credentials"] == "true"


def test_create_and_update_app(client: TestClient) -> None:
    client.post(
        "/v1/auth/login",
        json={"email": "admin@example.com", "password": "correct-password"},
    )
    created = client.post(
        "/v1/apps",
        json={"name": "Yeni Uygulama", "slug": "yeni-uygulama", "color": "#112233"},
    )
    assert created.status_code == 201
    assert created.json()["iosBundleId"] is None
    updated = client.patch(
        f"/v1/apps/{created.json()['id']}", json={"status": "live", "playStoreUrl": ""}
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "live"


def test_maps_routes_are_session_protected(client: TestClient) -> None:
    response = client.get("/v1/maps/jobs")
    assert response.status_code == 401


def test_creates_maps_job_through_service(client: TestClient) -> None:
    client.post(
        "/v1/auth/login",
        json={"email": "admin@example.com", "password": "correct-password"},
    )
    captured: dict[str, Any] = {}

    async def json_request(
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, object]:
        captured.update({"method": method, "path": path, "json": json, "params": params})
        return {"id": "4af2cabb-b7f8-4a90-a7a1-64bcc470592e", "status": "queued"}

    client.app.state.maps_service.json_request = json_request
    response = client.post(
        "/v1/maps/jobs",
        json={
            "keywords": [" kahve Kadıköy "],
            "language": "tr",
            "depth": 1,
            "maxTimeSeconds": 120,
        },
    )

    assert response.status_code == 202
    assert response.json()["status"] == "queued"
    assert captured["method"] == "POST"
    assert captured["path"] == "/jobs"
    assert captured["json"]["keywords"] == ["kahve Kadıköy"]
    assert captured["json"]["max_time_seconds"] == 120


def test_rejects_fast_maps_job_without_coordinates(client: TestClient) -> None:
    client.post(
        "/v1/auth/login",
        json={"email": "admin@example.com", "password": "correct-password"},
    )
    response = client.post(
        "/v1/maps/jobs",
        json={"keywords": ["eczane"], "fastMode": True},
    )
    assert response.status_code == 400


def test_root_entrypoint_starts_uvicorn(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, dict[str, object]]] = []
    monkeypatch.setenv("NODE_ENV", "test")
    monkeypatch.setenv("PORT", "4321")
    monkeypatch.setenv("ADMIN_PASSWORD", "correct-password")
    monkeypatch.setenv("SESSION_SECRET", "a" * 32)
    monkeypatch.setattr(
        entrypoint.uvicorn,
        "run",
        lambda app, **kwargs: calls.append((app, kwargs)),
    )

    entrypoint.main()

    assert calls == [
        (
            "app.main:create_app",
            {
                "factory": True,
                "host": "0.0.0.0",
                "port": 4321,
                "reload": False,
                "proxy_headers": True,
            },
        )
    ]
