from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from uzwatermu.db.connection import connect


class SettingsRepository:
    """Admin bot ichida o'zgartiradigan parametrlar. Qiymatlar JSON ko'rinishida saqlanadi."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    def get(self, key: str, default: Any = None) -> Any:
        with connect(self.db_path) as db:
            row = db.execute("select value from settings where key = ?", (key,)).fetchone()
        return json.loads(row["value"]) if row else default

    def set(self, key: str, value: Any, updated_by: int | None) -> None:
        with connect(self.db_path) as db:
            db.execute(
                """
                insert into settings (key, value, updated_by) values (?, ?, ?)
                on conflict(key) do update set
                    value = excluded.value,
                    updated_by = excluded.updated_by,
                    updated_at = current_timestamp
                """,
                (key, json.dumps(value, ensure_ascii=False), updated_by),
            )
