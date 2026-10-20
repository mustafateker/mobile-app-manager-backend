from typing import Any

from pydantic import BaseModel, ConfigDict


class AsoStatusDto(BaseModel):
    model_config = ConfigDict(extra="allow")

    configured: bool
    connected: bool
    details: dict[str, Any] | None = None
    error: str | None = None

