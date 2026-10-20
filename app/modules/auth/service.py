from __future__ import annotations

import hashlib
import hmac
import time
from collections import defaultdict, deque

from app.config import Settings
from app.modules.auth.dto import LoginDto, SessionDto, UserDto

PASSWORD_SALT = b"mobil-app-manager-v1"


class AuthService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @staticmethod
    def _digest(value: str) -> bytes:
        scrypt = getattr(hashlib, "scrypt", None)
        if scrypt is not None:
            return scrypt(
                value.encode(), salt=PASSWORD_SALT, n=16384, r=8, p=1, dklen=64
            )
        return hashlib.pbkdf2_hmac("sha256", value.encode(), PASSWORD_SALT, 200_000, dklen=64)

    def authenticate(self, credentials: LoginDto) -> SessionDto | None:
        email_matches = hmac.compare_digest(
            credentials.email.lower().encode(), self.settings.admin_email.lower().encode()
        )
        password_matches = hmac.compare_digest(
            self._digest(credentials.password), self._digest(self.settings.admin_password)
        )
        if not email_matches or not password_matches:
            return None
        return self.session()

    def session(self) -> SessionDto:
        return SessionDto(user=UserDto(email=self.settings.admin_email))


class LoginRateLimiter:
    def __init__(self, limit: int = 8, window_seconds: int = 900) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self._attempts: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        attempts = self._attempts[key]
        while attempts and attempts[0] <= now - self.window_seconds:
            attempts.popleft()
        if len(attempts) >= self.limit:
            return False
        attempts.append(now)
        return True
