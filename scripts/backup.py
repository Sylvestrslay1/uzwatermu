"""Kunlik backup: python scripts/backup.py  (Task Scheduler / cron orqali chaqiriladi)."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import datetime, timedelta

from uzwatermu.config import Settings


def main() -> None:
    settings = Settings()
    settings.ensure_dirs()
    target = settings.backup_dir / f"bot_{datetime.now():%Y%m%d_%H%M%S}.sqlite3"
    with (
        closing(sqlite3.connect(settings.database_path)) as src,
        closing(sqlite3.connect(target)) as dst,
    ):
        src.backup(dst)
    cutoff = datetime.now() - timedelta(days=settings.backup_keep_days)
    for old in settings.backup_dir.glob("bot_*.sqlite3"):
        if datetime.fromtimestamp(old.stat().st_mtime) < cutoff:
            old.unlink()
    print(f"Backup: {target}")


if __name__ == "__main__":
    main()
