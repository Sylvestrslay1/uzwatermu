from __future__ import annotations

from pathlib import Path

from uzwatermu.db.connection import connect


class AccountLinkRepository:
    """Telegram ID ↔ hisob raqam bog'lanishlari. Abonentning shaxsiy ma'lumoti bu yerda yo'q."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    def has_approved(self, telegram_id: int) -> bool:
        with connect(self.db_path) as db:
            row = db.execute(
                "select 1 from account_links where telegram_id = ? and status = 'approved' limit 1",
                (telegram_id,),
            ).fetchone()
        return row is not None
