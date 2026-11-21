from __future__ import annotations

import secrets
from typing import Any

import httpx


class TrinkowAdminError(Exception):
    def __init__(self, message: str, status_code: int = 502) -> None:
        super().__init__(message)
        self.status_code = status_code


class TrinkowAdminAuthError(TrinkowAdminError):
    def __init__(self, message: str = "Geçersiz yönetici şifresi.") -> None:
        super().__init__(message, status_code=401)


class TrinkowAdminService:
    def __init__(
        self,
        base_url: str,
        admin_token: str,
        admin_password: str,
    ) -> None:
        self._base_url = str(base_url).rstrip("/")
        self._admin_token = admin_token.strip()
        self._admin_password = admin_password

    @property
    def configured(self) -> bool:
        return bool(self._base_url and self._admin_token)

    def _headers(self) -> dict[str, str]:
        return {
            "X-Admin-Token": self._admin_token,
            "User-Agent": "MobileAppManager/1.0",
            "Accept": "application/json",
        }

    async def list_users(
        self,
        search: str | None = None,
        filter_type: str | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> dict[str, Any]:
        if not self.configured:
            raise TrinkowAdminError(
                "Trinkow admin servisi yapılandırılmamış (API base URL veya token eksik).", 503
            )

        params: dict[str, Any] = {"page": page, "limit": limit}
        if search and search.strip():
            params["q"] = search.strip()
        if filter_type and filter_type != "all":
            params["filter"] = filter_type

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.get(
                    f"{self._base_url}/v1/admin/users",
                    params=params,
                    headers=self._headers(),
                )
        except httpx.HTTPError as error:
            raise TrinkowAdminError(f"Trinkow sunucusuna bağlanılamadı: {error}", 502) from error

        if res.status_code != 200:
            raise TrinkowAdminError(
                f"Trinkow API hatası ({res.status_code}): {res.text}",
                res.status_code if 400 <= res.status_code < 500 else 502,
            )

        return res.json()

    async def update_user_status(self, user_id: str, askida: bool) -> dict[str, Any]:
        if not self.configured:
            raise TrinkowAdminError("Trinkow admin servisi yapılandırılmamış.", 503)

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.patch(
                    f"{self._base_url}/v1/admin/users/{user_id}/status",
                    json={"askida": askida},
                    headers=self._headers(),
                )
        except httpx.HTTPError as error:
            raise TrinkowAdminError(f"Trinkow sunucusuna bağlanılamadı: {error}", 502) from error

        if res.status_code != 200:
            raise TrinkowAdminError(
                f"Kullanıcı durumu güncellenemedi ({res.status_code}): {res.text}",
                res.status_code if 400 <= res.status_code < 500 else 502,
            )

        return res.json()

    async def delete_user(self, user_id: str, admin_password: str) -> dict[str, Any]:
        if not self.configured:
            raise TrinkowAdminError("Trinkow admin servisi yapılandırılmamış.", 503)

        # RE-AUTHENTICATION CHECK: Every delete request MUST verify admin password!
        if not admin_password or not secrets.compare_digest(admin_password, self._admin_password):
            raise TrinkowAdminAuthError(
                "Geçersiz yönetici şifresi. Silme işlemi için kimlik doğrulaması başarısız."
            )

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                res = await client.delete(
                    f"{self._base_url}/v1/admin/users/{user_id}",
                    headers=self._headers(),
                )
        except httpx.HTTPError as error:
            raise TrinkowAdminError(f"Trinkow sunucusuna bağlanılamadı: {error}", 502) from error

        if res.status_code != 200:
            raise TrinkowAdminError(
                f"Kullanıcı silinemedi ({res.status_code}): {res.text}",
                res.status_code if 400 <= res.status_code < 500 else 502,
            )

        return res.json()
