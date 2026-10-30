from __future__ import annotations

from pathlib import Path

from uzwatermu.db.connection import connect

STAFF_ROLES = frozenset({"operator", "inspector", "admin"})


class UserRepository:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    def get(self, telegram_id: int) -> dict | None:
        with connect(self.db_path) as db:
            row = db.execute(
                "select * from users where telegram_id = ?", (telegram_id,)
            ).fetchone()
        return dict(row) if row else None

    def set_language(self, telegram_id: int, language: str) -> None:
        with connect(self.db_path) as db:
            db.execute(
                """
                insert into users (telegram_id, language) values (?, ?)
                on conflict(telegram_id) do update set
                    language = excluded.language, updated_at = current_timestamp
                """,
                (telegram_id, language),
            )

    def set_role(self, telegram_id: int, role: str) -> None:
        with connect(self.db_path) as db:
            db.execute(
                """
                insert into users (telegram_id, role) values (?, ?)
                on conflict(telegram_id) do update set
                    role = excluded.role, updated_at = current_timestamp
                """,
                (telegram_id, role),
            )
