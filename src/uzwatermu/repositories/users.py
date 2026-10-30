from __future__ import annotations

from pathlib import Path

from uzwatermu.db.connection import connect


class UserRepository:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    def upsert_language(self, telegram_id: int, language: str) -> None:
        with connect(self.db_path) as db:
            db.execute(
                """
                insert into users (telegram_id, language) values (?, ?)
                on conflict(telegram_id) do update set language = excluded.language
                """,
                (telegram_id, language),
            )

    def get(self, telegram_id: int) -> dict | None:
        with connect(self.db_path) as db:
            row = db.execute("select * from users where telegram_id = ?", (telegram_id,)).fetchone()
        return dict(row) if row else None

    def role(self, telegram_id: int) -> str:
        user = self.get(telegram_id)
        return user["role"] if user else "user"

    def set_role(self, telegram_id: int, role: str) -> None:
        with connect(self.db_path) as db:
            db.execute(
                """
                insert into users (telegram_id, role) values (?, ?)
                on conflict(telegram_id) do update set role = excluded.role
                """,
                (telegram_id, role),
            )
