from __future__ import annotations

import os
from typing import Mapping

from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, ValidationError, field_validator


class Settings(BaseModel):
    model_config = ConfigDict(extra="ignore")

    node_env: str = "development"
    port: int = Field(default=4100, gt=0)
    database_path: str = "./data/manager.sqlite"
    admin_email: str = "admin@triworkster.com"
    admin_password: str = Field(min_length=10)
    session_secret: str = Field(min_length=32)
    session_same_site: str = "lax"
    web_origin: HttpUrl = HttpUrl("http://localhost:5173")
    asobeast_base_url: HttpUrl = HttpUrl("http://127.0.0.1:3001/api/backend")
    asobeast_api_token: str = ""
    maps_base_url: HttpUrl = HttpUrl("http://127.0.0.1:8000")
    maps_api_key: str = ""
    posthog_host: HttpUrl = HttpUrl("https://eu.i.posthog.com")
    posthog_project_id: str = "333929"
    posthog_personal_api_key: str = ""

    @field_validator("node_env")
    @classmethod
    def validate_environment(cls, value: str) -> str:
        if value not in {"development", "test", "production"}:
            raise ValueError("NODE_ENV development, test veya production olmalıdır")
        return value

    @field_validator("admin_email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        if "@" not in value or value.startswith("@") or value.endswith("@"):
            raise ValueError("ADMIN_EMAIL geçerli bir e-posta olmalıdır")
        return value

    @field_validator("session_same_site")
    @classmethod
    def validate_same_site(cls, value: str) -> str:
        normalized = value.lower()
        if normalized not in {"lax", "strict", "none"}:
            raise ValueError("SESSION_SAME_SITE lax, strict veya none olmalıdır")
        return normalized


def read_settings(env: Mapping[str, str] | None = None) -> Settings:
    if env is None:
        load_dotenv()
    source = os.environ if env is None else env
    values = {
        "node_env": source.get("NODE_ENV", "development"),
        "port": source.get("PORT", "4100"),
        "database_path": source.get("DATABASE_PATH", "./data/manager.sqlite"),
        "admin_email": source.get("ADMIN_EMAIL", "admin@triworkster.com"),
        "admin_password": source.get("ADMIN_PASSWORD"),
        "session_secret": source.get("SESSION_SECRET"),
        "session_same_site": source.get("SESSION_SAME_SITE", "lax"),
        "web_origin": source.get("WEB_ORIGIN", "http://localhost:5173"),
        "asobeast_base_url": source.get(
            "ASOBEAST_BASE_URL", "http://127.0.0.1:3001/api/backend"
        ),
        "asobeast_api_token": source.get("ASOBEAST_API_TOKEN", ""),
        "maps_base_url": source.get("MAPS_BASE_URL", "http://127.0.0.1:8000"),
        "maps_api_key": source.get("MAPS_API_KEY", ""),
        "posthog_host": source.get("POSTHOG_HOST", "https://eu.i.posthog.com"),
        "posthog_project_id": source.get("POSTHOG_PROJECT_ID", "333929"),
        "posthog_personal_api_key": source.get("POSTHOG_PERSONAL_API_KEY", ""),
    }
    return Settings.model_validate(values)


__all__ = ["Settings", "ValidationError", "read_settings"]
