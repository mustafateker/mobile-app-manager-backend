from __future__ import annotations

from typing import Any
from urllib.parse import quote

import httpx


class AsoBeastError(Exception):
    def __init__(self, status_code: int | None, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code


class AsoBeastService:
    def __init__(self, base_url: str, token: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token

    @property
    def configured(self) -> bool:
        return self.token.startswith("asob_")

    async def request(
        self, method: str, path: str, json: dict[str, Any] | None = None
    ) -> Any:
        if not self.configured:
            raise AsoBeastError(None, "AsoBeast API token henüz tanımlanmadı.")
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.request(
                    method,
                    f"{self.base_url}{path}",
                    headers={"authorization": f"Bearer {self.token}"},
                    json=json,
                )
        except httpx.HTTPError as error:
            raise AsoBeastError(502, "AsoBeast isteği başarısız oldu.") from error
        if response.is_error:
            message = "AsoBeast isteği başarısız oldu."
            try:
                body = response.json()
                if isinstance(body, dict) and isinstance(body.get("message"), str):
                    message = body["message"]
            except ValueError:
                pass
            raise AsoBeastError(response.status_code, message)
        return response.json() if response.content else None

    async def status(self) -> dict[str, Any]:
        return await self.request("GET", "/ai/status")

    async def apps(self) -> list[dict[str, Any]]:
        return await self.request("GET", "/apps")

    async def summary(self, app_id: str) -> dict[str, Any]:
        return await self.request("GET", f"/apps/{quote(app_id, safe='')}/summary")

    async def audit(self, app_id: str) -> dict[str, Any]:
        return await self.request("GET", f"/apps/{quote(app_id, safe='')}/audit")

    async def keywords(self, app_id: str) -> list[dict[str, Any]]:
        return await self.request("GET", f"/apps/{quote(app_id, safe='')}/keywords")

    async def import_app(self, url: str) -> dict[str, Any]:
        return await self.request("POST", "/apps", {"url": url})

    async def run_daily(self, app_id: str) -> dict[str, Any]:
        return await self.request("POST", f"/apps/{quote(app_id, safe='')}/run-daily", {})

