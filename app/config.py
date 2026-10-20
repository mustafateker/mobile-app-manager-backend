from __future__ import annotations

import os
from typing import Mapping

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, ValidationError, field_validator


class Settings(BaseModel):
    model_config = ConfigDict(extra="ignore")

    node_env: str = "development"
    port: int = Field(default=4100, gt=0)
    database_path: str = "./data/manager.sqlite"
    admin_email: str = "admin@triworkster.com"
    admin_password: str = Field(min_length=10)
    session_secret: str = Field(min_length=32)
    web_origin: HttpUrl = HttpUrl("http://localhost:5173")
    asobeast_base_url: HttpUrl = HttpUrl("http://127.0.0.1:3001/api/backend")
    asobeast_api_token: str = ""

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


def read_settings(env: Mapping[str, str] | None = None) -> Settings:
    source = os.environ if env is None else env
    values = {
        "node_env": source.get("NODE_ENV", "development"),
        "port": source.get("PORT", "4100"),
        "database_path": source.get("DATABASE_PATH", "./data/manager.sqlite"),
        "admin_email": source.get("ADMIN_EMAIL", "admin@triworkster.com"),
        "admin_password": source.get("ADMIN_PASSWORD"),
        "session_secret": source.get("SESSION_SECRET"),
        "web_origin": source.get("WEB_ORIGIN", "http://localhost:5173"),
        "asobeast_base_url": source.get(
            "ASOBEAST_BASE_URL", "http://127.0.0.1:3001/api/backend"
        ),
        "asobeast_api_token": source.get("ASOBEAST_API_TOKEN", ""),
    }
    return Settings.model_validate(values)


__all__ = ["Settings", "ValidationError", "read_settings"]

