from __future__ import annotations

from pathlib import Path

from uzwatermu.db.connection import connect
from uzwatermu.security.masking import sanitize_audit_details


class AuditRepository:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    def write(self, actor_id: int | None, action: str, details: str = "") -> None:
        with connect(self.db_path) as db:
            db.execute(
                "insert into audit_log (actor_id, action, details) values (?, ?, ?)",
                (actor_id, action, sanitize_audit_details(details)),
            )
