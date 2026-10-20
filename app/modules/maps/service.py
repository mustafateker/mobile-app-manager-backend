from __future__ import annotations

from typing import Any

import httpx


class MapsServiceError(Exception):
    def __init__(self, status_code: int | None, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code


class MapsService:
    def __init__(self, base_url: str, api_key: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    @property
    def configured(self) -> bool:
        return bool(self.base_url and self.api_key)

    async def request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> httpx.Response:
        if not self.configured:
            raise MapsServiceError(None, "Google Maps scraper bağlantısı henüz tanımlanmadı.")
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.request(
                    method,
                    f"{self.base_url}{path}",
                    headers={"X-API-Key": self.api_key},
                    json=json,
                    params=params,
                )
        except httpx.HTTPError as error:
            raise MapsServiceError(None, "Google Maps scraper servisine ulaşılamadı.") from error
        if response.is_error:
            message = "Google Maps scraper isteği başarısız oldu."
            try:
                body = response.json()
                if isinstance(body, dict):
                    detail = body.get("detail") or body.get("message")
                    if isinstance(detail, str):
                        message = detail
            except ValueError:
                if response.text.strip():
                    message = response.text.strip()
            raise MapsServiceError(response.status_code, message)
        return response

    async def json_request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        response = await self.request(method, path, json=json, params=params)
        return response.json() if response.content else None

    async def health(self) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{self.base_url}/health")
                response.raise_for_status()
                return response.json()
        except (httpx.HTTPError, ValueError) as error:
            raise MapsServiceError(None, "Google Maps scraper servisine ulaşılamadı.") from error
