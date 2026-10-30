from __future__ import annotations

from pathlib import Path

from uzwatermu.db.connection import connect


class AbonentRepository:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    def find(self, account: str) -> dict | None:
        with connect(self.db_path) as db:
            row = db.execute("select * from abonents where account = ?", (account,)).fetchone()
        return dict(row) if row else None

    def replace_all(self, rows: list[dict]) -> int:
        """Import: barcha abonentlarni bitta tranzaksiyada almashtiradi."""
        columns = (
            "account", "fio", "phone", "address", "area",
            "inspector_fio", "inspector_phone", "debit", "credit",
        )
        with connect(self.db_path) as db:
            db.execute(
                "delete from abonents where account not in (select account from user_accounts)"
            )
            db.executemany(
                f"""
                insert into abonents ({", ".join(columns)}) values ({", ".join("?" * len(columns))})
                on conflict(account) do update set
                {", ".join(f"{c} = excluded.{c}" for c in columns[1:])},
                imported_at = current_timestamp
                """,  # noqa: S608 - ustun nomlari yuqoridagi qat'iy ro'yxatdan
                [tuple(row.get(c, "") for c in columns) for row in rows],
            )
        return len(rows)
