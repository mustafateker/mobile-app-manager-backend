from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.database import Database
from app.modules.apps.dto import CreateAppDto, ManagedAppDto, UpdateAppDto

SELECT_APPS = """
SELECT id, name, slug, ios_bundle_id, android_package, app_store_url,
       play_store_url, asobeast_app_id, color, status, created_at, updated_at
FROM managed_apps
"""


class AppService:
    def __init__(self, database: Database) -> None:
        self.database = database
        self._seed()

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    @staticmethod
    def _from_row(row: sqlite3.Row) -> ManagedAppDto:
        return ManagedAppDto.model_validate(dict(row))

    def _seed(self) -> None:
        now = self._now()
        values = [
            (
                str(uuid4()), "Koçum Benim", "kocum-benim",
                "com.triworkster.kocumbenimmobileapp",
                "com.triworkster.kocumbenimmobileapp", None,
                "https://play.google.com/store/apps/details?id=com.triworkster.kocumbenimmobileapp",
                None, "#f97316", "development", now, now,
            ),
            (
                str(uuid4()), "Trinkow", "trinkow", None, None, None, None,
                None, "#7c3aed", "development", now, now,
            ),
        ]
        self.database.connection.executemany(
            """
            INSERT OR IGNORE INTO managed_apps
            (id, name, slug, ios_bundle_id, android_package, app_store_url,
             play_store_url, asobeast_app_id, color, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            values,
        )
        self.database.connection.commit()

    def list(self) -> list[ManagedAppDto]:
        rows = self.database.connection.execute(f"{SELECT_APPS} ORDER BY created_at").fetchall()
        return [self._from_row(row) for row in rows]

    def find(self, app_id: UUID) -> ManagedAppDto | None:
        row = self.database.connection.execute(
            f"{SELECT_APPS} WHERE id = ?", (str(app_id),)
        ).fetchone()
        return self._from_row(row) if row else None

    def create(self, payload: CreateAppDto) -> ManagedAppDto:
        app_id = uuid4()
        now = self._now()
        values = payload.model_dump(mode="json")
        self.database.connection.execute(
            """
            INSERT INTO managed_apps
            (id, name, slug, ios_bundle_id, android_package, app_store_url,
             play_store_url, asobeast_app_id, color, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(app_id), values["name"], values["slug"], values["ios_bundle_id"],
                values["android_package"], values["app_store_url"], values["play_store_url"],
                values["asobeast_app_id"], values["color"], values["status"], now, now,
            ),
        )
        self.database.connection.commit()
        return self.find(app_id)  # type: ignore[return-value]

    def update(self, app_id: UUID, payload: UpdateAppDto) -> ManagedAppDto | None:
        current = self.find(app_id)
        if current is None:
            return None
        changes = payload.model_dump(exclude_unset=True, mode="json")
        if not changes:
            return current
        columns = {key: key for key in changes}
        assignments = ", ".join(f"{columns[key]} = ?" for key in changes)
        values = [changes[key] for key in changes]
        self.database.connection.execute(
            f"UPDATE managed_apps SET {assignments}, updated_at = ? WHERE id = ?",
            (*values, self._now(), str(app_id)),
        )
        self.database.connection.commit()
        return self.find(app_id)

    def link_asobeast(self, app_id: UUID, remote_id: str) -> ManagedAppDto | None:
        return self.update(app_id, UpdateAppDto(asobeast_app_id=remote_id))
